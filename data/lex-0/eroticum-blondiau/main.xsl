<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    exclude-result-prefixes="xs"
    version="2.0">
    <xsl:output method="html" indent="yes"/>
    
    
    <xsl:template match="/">
        <html>
            <head>
            </head>
            <body>
                <div style="max-width: 600px; margin: 0px auto; x-column-count: 2; x-column-gap: 40px;">
                    <xsl:apply-templates select="/tei:TEI/tei:text/tei:body/*"/>
                </div>
            </body>
        </html>
    </xsl:template>
    
    
    <!--top-level entry element: basically just a paragraph-->
    <xsl:template match="tei:superEntry | tei:entry | tei:entryFree">
        <div>
            <xsl:attribute name="id" select="@xml:id"/>
            <xsl:apply-templates/>
        </div>
    </xsl:template>
    
    <xsl:template match="tei:form">
        <b><xsl:apply-templates/></b>
    </xsl:template>
    
    <xsl:template match="tei:ref[@target]">
        <xsl:text> </xsl:text>
        <b><xsl:apply-templates/></b>
    </xsl:template>
    
    <xsl:template match="tei:author">
        <i><xsl:apply-templates/></i>
    </xsl:template>
    
    
    
    <xsl:template match="tei:form[@type='lemma' or @type='variant']/tei:orth">
        <b><xsl:apply-templates/></b>
    </xsl:template>
    <xsl:template match="tei:gramGrp">
        <i><xsl:apply-templates /></i>
    </xsl:template>
    <xsl:template match="tei:gram[not(text())]">
        <span style="font-style: normal;"><xsl:value-of select="@value"/></span>
    </xsl:template>
    
    <xsl:template match="tei:cit/tei:quote">
        <i><xsl:apply-templates/></i>
    </xsl:template>
    <xsl:template match="tei:mentioned">
        <i><xsl:apply-templates/></i>
    </xsl:template>
    <xsl:template match="tei:sense">
        <p>
            <xsl:attribute name="id" select="@xml:id"/>
            <xsl:if test="contains(@xml:id, '1')">
                <xsl:attribute name="style">display:inline;</xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
        </p>
    </xsl:template>
    <xsl:template match="tei:quote"><i><xsl:apply-templates/></i></xsl:template>
    <xsl:template match="*[@rend='italic']">
        <i><xsl:apply-templates/></i>
    </xsl:template>
    <xsl:template match="tei:lb"><br /></xsl:template>
</xsl:stylesheet>
