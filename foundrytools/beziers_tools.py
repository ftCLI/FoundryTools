from beziers.path import BezierPath
from beziers.path.representations import Nodelist
from fontTools.misc.psCharStrings import T2CharString
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont


def handle_curve_nodes(pen: T2CharStringPen, nodes_list: Nodelist, i: int) -> int:
    """
    Handles the curve nodes in a BezierPath.

    :param pen: The T2CharStringPen.
    :type pen: T2CharStringPen
    :param nodes_list: The list of nodes in the path.
    :type nodes_list: Nodelist
    :param i: The index of the current node.
    :type i: int
    :return: The index of the next node to process.
    :rtype: int
    """

    curve_points = []
    while i < len(nodes_list) and nodes_list[i].type in {"offcurve", "curve"}:
        curve_points.append((nodes_list[i].x, nodes_list[i].y))
        if nodes_list[i].type == "curve":  # Curve node ends the sequence
            pen.curveTo(*curve_points)
            break
        i += 1
    return i + 1  # Ensure the "curve" node is not processed again


def draw_bez(pen: T2CharStringPen, paths: list[BezierPath]) -> None:
    """
    Draws a list of Bezier paths using a T2CharStringPen.

    :param pen: The T2CharStringPen.
    :type pen: T2CharStringPen
    :param paths: The list of Bezier paths.
    :type paths: list
    """
    for path in paths:
        nodes_list = path.asNodelist()
        pen.moveTo((nodes_list[0].x, nodes_list[0].y))
        i = 1
        while i < len(nodes_list):
            node = nodes_list[i]
            if node.type == "move":
                pen.moveTo((node.x, node.y))
                i += 1
            elif node.type == "line":
                pen.lineTo((node.x, node.y))
                i += 1
            elif node.type in {"offcurve", "curve"}:
                i = handle_curve_nodes(pen, nodes_list, i)
            else:
                raise ValueError(f"Unknown node type: {node.type}")


def bez_to_charstring(paths: list[BezierPath], font: TTFont, glyph_name: str) -> T2CharString:
    """
    Converts a list of Bezier paths to a T2CharString.

    :param paths: The list of Bezier paths.
    :type paths: list
    :param font: The font.
    :type font: TTFont
    :param glyph_name: The name of the glyph.
    :type glyph_name: str
    :return: The T2CharString.
    :rtype: T2CharString
    """
    glyph_set = font.getGlyphSet()
    pen = T2CharStringPen(width=glyph_set[glyph_name].width, glyphSet=glyph_set)
    draw_bez(paths=paths, pen=pen)
    charstring = pen.getCharString()
    return charstring


def add_extremes(font: TTFont) -> dict[str, T2CharString]:
    """
    Adds extremes to the curves in the font's glyphs.

    :param font: A TTFont object representing the font from which to retrieve glyphs.
    :type font: TTFont
    :return: A dictionary mapping glyph names to their corresponding T2CharString objects with added
        extremes.
    :rtype: dict[str, T2CharString]
    """
    glyph_set = font.getGlyphSet()
    charstrings = {}
    for k in glyph_set:
        bezier_paths: list[BezierPath] = BezierPath.fromFonttoolsGlyph(font, glyphname=k)
        for bp in bezier_paths:
            bp.addExtremes()
        charstring: T2CharString = bez_to_charstring(bezier_paths, font, glyph_name=k)
        charstrings[k] = charstring

    return charstrings
