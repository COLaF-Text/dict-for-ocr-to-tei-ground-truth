#!/usr/bin/env python
"""
Draws a transparent overlay of the forced alignment output over the input
image.
"""
import regex
import os
import click
import unicodedata
from lxml import etree
from itertools import cycle
from unicodedata import normalize
from kraken.serialization import max_bbox
cmap = cycle([(230, 25, 75, 127),
              (60, 180, 75, 127),
              (255, 225, 25, 127),
              (0, 130, 200, 127),
              (245, 130, 48, 127),
              (145, 30, 180, 127),
              (70, 240, 240, 127)])


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = unicodedata.normalize('NFKD', value)
    value = regex.sub(r'[^\w\s-]', '', value).strip().lower()
    value = regex.sub(r'[-\s]+', '-', value)
    return value


def _repl_alto(fname, cuts):
    with open(fname, 'rb') as fp:
        doc = etree.parse(fp)
        lines = doc.findall('.//{*}TextLine')
        seg_idx_total = 0
        for line, record in zip(lines, cuts):
            idx = 0

            # remove textual tags
            for chld in line:
                if chld.tag.endswith('String'):
                    line.remove(chld)
                if chld.tag.endswith('SP'):
                    line.remove(chld)

            segments = regex.split(r'(\s+)', "".join(record.prediction))
            line_offset = 0
            for seg_idx, segment in enumerate(segments):
                if len(segment) == 0:
                    continue
                elif not segment.strip() and seg_idx == 0:  # ALTO forbids Space as first char.
                    line_offset += 1
                    continue
                # <String ID="segment_{{ segment.index }}" CONTENT="{{ segment.text|e }}" HPOS="{{ segment.bbox[0] }}" VPOS="{{ segment.bbox[1] }}" WIDTH="{{ segment.bbox[2] - segment.bbox[0] }}" HEIGHT="{{ segment.bbox[3] - segment.bbox[1] }}" WC="{{ (segment.confidences|sum / segment.confidences|length)|round(4) }}">
                else:
                    seg_cuts = record.cuts[line_offset:line_offset + len(segment)]
                    seg_bbox = max_bbox(seg_cuts)

                    if not segment.strip():
                        sp = etree.SubElement(line, "SP")
                    else:
                        sp = etree.SubElement(line, "String")
                        sp.set("CONTENT", segment)

                    sp.set("ID", f"tok_{seg_idx_total}")
                    sp.set("HPOS", f"{seg_bbox[0]}")
                    sp.set("VPOS", f"{seg_bbox[1]}")
                    sp.set("WIDTH", f"{seg_bbox[2] - seg_bbox[0]}")
                    sp.set("HEIGHT", f"{seg_bbox[3] - seg_bbox[1]}")
                    line_offset += len(segment)
                    seg_idx_total += 1

        with open(f'{os.path.basename(fname)}_algn.xml', 'wb') as fp:
            doc.write(fp, encoding='UTF-8', xml_declaration=True)


def _repl_page(fname, cuts):
    with open(fname, 'rb') as fp:
        doc = etree.parse(fp)
        lines = doc.findall('.//{*}TextLine')
        for line, line_cuts in zip(lines, cuts):
            glyphs = line.findall('../{*}Glyph/{*}Coords')
            for glyph, cut in zip(glyphs, line_cuts):
                glyph.attrib['points'] = ' '.join([','.join([str(x) for x in pt]) for pt in cut])
        with open(f'{os.path.basename(fname)}_algn.xml', 'wb') as fp:
            doc.write(fp, encoding='UTF-8', xml_declaration=True)


@click.command()
@click.option('-f', '--format-type', type=click.Choice(['alto', 'page']), default='page',
              help='Sets the input document format. In ALTO and PageXML mode all '
              'data is extracted from xml files containing both baselines, polygons, and a '
              'link to source images.')
@click.option('-i', '--model', default=None, show_default=True, type=click.Path(exists=True),
              help='Transcription model to use.')
@click.option('-u', '--normalization', show_default=True, type=click.Choice(['NFD', 'NFKD', 'NFC', 'NFKC']),
              default=None,
              help='Ground truth normalization')
@click.option('-o', '--output', type=click.Choice(['xml', 'overlay']),
              show_default=True, default='overlay', help='Output mode. Either page or '
              'alto for xml output, overlay for image overlays.')
@click.argument('files', nargs=-1)
def cli(format_type, model, normalization, output, files):
    """
    A script producing overlays of lines and regions from either ALTO or
    PageXML files or run a model to do the same.
    """
    if len(files) == 0:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()

    from PIL import Image, ImageDraw

    from kraken.lib import models, xml
    from kraken import align

    if format_type == 'alto':
        fn = xml.parse_alto
        repl_fn = _repl_alto
    else:
        fn = xml.parse_page
        repl_fn = _repl_page
    click.echo(f'Loading model {model}')
    net = models.load_any(model)

    for doc in files:
        click.echo(f'Processing {doc} ', nl=False)
        data = fn(doc)
        if normalization:
            for line in data["lines"]:
                line["text"] = normalize(normalization, line["text"])
        im = Image.open(data['image']).convert('RGBA')
        records = align.forced_align(data, net)
        if output == 'overlay':
            tmp = Image.new('RGBA', im.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(tmp)
            for record in records:
                for pol in record.cuts:
                    c = next(cmap)
                    draw.polygon([tuple(x) for x in pol], fill=c, outline=c[:3])
            base_image = Image.alpha_composite(im, tmp)
            base_image.save(f'high_{os.path.basename(doc)}_algn.png')
        else:
            repl_fn(doc, records)
        click.secho('\u2713', fg='green')


if __name__ == '__main__':
    cli()
