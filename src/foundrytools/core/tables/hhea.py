import math
from copy import deepcopy
from typing import Optional, Union

from fontTools.misc.roundTools import otRound
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._h_h_e_a import table__h_h_e_a

from foundrytools.constants import T_HEAD, T_HHEA, T_POST
from foundrytools.core.tables.default import DefaultTbl


class HheaTable(DefaultTbl):
    """This class extends the fontTools ``hhea`` tables."""

    def __init__(self, ttfont: TTFont) -> None:
        """
        Initializes the ``hhea`` table handler.

        :param ttfont: The ``TTFont`` object.
        :type ttfont: TTFont
        """
        super().__init__(ttfont=ttfont, table_tag=T_HHEA)
        self._copy = deepcopy(self.table)

    @property
    def table(self) -> table__h_h_e_a:
        """
        The wrapped ``table__h_h_e_a`` table object.
        """
        return self._table

    @table.setter
    def table(self, value: table__h_h_e_a) -> None:
        """
        Wraps a new ``table__h_h_e_a`` object.
        """
        self._table = value

    @property
    def is_modified(self) -> bool:
        """
        A read-only property that returns whether the ``hhea`` table has been modified.

        :return: Whether the ``hhea`` table has been modified.
        :rtype: bool
        """
        return self._copy.compile(self.ttfont) != self.table.compile(self.ttfont)

    @property
    def ascent(self) -> int:
        """
        A property with getter and setter for the ``ascent`` field of the ``hhea`` table.

        :return: The ``ascent`` value.
        :rtype: int
        """
        return self.table.ascent

    @ascent.setter
    def ascent(self, value: int) -> None:
        """Sets the ``ascent`` field of the ``hhea`` table."""
        self.table.ascent = value

    @property
    def descent(self) -> int:
        """
        A property with getter and setter for the ``descent`` field of the ``hhea`` table.

        :return: The ``descent`` value.
        :rtype: int
        """
        return self.table.descent

    @descent.setter
    def descent(self, value: int) -> None:
        """Sets the ``descent`` field of the ``hhea`` table."""
        self.table.descent = value

    @property
    def line_gap(self) -> int:
        """
        A property with getter and setter for the ``lineGap`` field of the ``hhea`` table.

        :return: The ``lineGap`` value.
        :rtype: int
        """
        return self.table.lineGap

    @line_gap.setter
    def line_gap(self, value: int) -> None:
        """Sets the ``lineGap`` field of the ``hhea`` table."""
        self.table.lineGap = value

    @property
    def advance_width_max(self) -> int:
        """
        A property with getter and setter for the ``advanceWidthMax`` field of the ``hhea`` table.

        :return: The ``advanceWidthMax`` value.
        :rtype: int
        """
        return self.table.advanceWidthMax

    @advance_width_max.setter
    def advance_width_max(self, value: int) -> None:
        """Sets the ``advanceWidthMax`` field of the ``hhea`` table."""
        self.table.advanceWidthMax = value

    @property
    def min_left_side_bearing(self) -> int:
        """
        A read-only property for the ``minLeftSideBearing`` field of the ``hhea`` table.

        :return: The ``minLeftSideBearing`` value.
        :rtype: int
        """
        return self.table.minLeftSideBearing

    @property
    def min_right_side_bearing(self) -> int:
        """
        A read-only property for the ``minRightSideBearing`` field of the ``hhea`` table.

        :return: The ``minRightSideBearing`` value.
        :rtype: int
        """
        return self.table.minRightSideBearing

    @property
    def x_max_extent(self) -> int:
        """
        A read-only property for the ``xMaxExtent`` field of the ``hhea`` table.

        :return: The ``xMaxExtent`` value.
        :rtype: int
        """
        return self.table.xMaxExtent

    @property
    def caret_slope_rise(self) -> int:
        """
        A property with getter and setter for the ``caretSlopeRise`` field of the ``hhea`` table.

        :return: The ``caretSlopeRise`` value.
        :rtype: int
        """
        return self.table.caretSlopeRise

    @caret_slope_rise.setter
    def caret_slope_rise(self, value: int) -> None:
        """Sets the ``caretSlopeRise`` field of the ``hhea`` table."""
        self.table.caretSlopeRise = value

    @property
    def caret_slope_run(self) -> int:
        """
        A property with getter and setter for the ``caretSlopeRun`` field of the ``hhea`` table.

        :return: The ``caretSlopeRun`` value.
        :rtype: int
        """
        return self.table.caretSlopeRun

    @caret_slope_run.setter
    def caret_slope_run(self, value: int) -> None:
        """Sets the ``caretSlopeRun`` field of the ``hhea`` table."""
        self.table.caretSlopeRun = value

    @property
    def caret_offset(self) -> int:
        """
        A property with getter and setter for the ``caretOffset`` field of the ``hhea`` table.

        :return: The ``caretOffset`` value.
        :rtype: int
        """
        return self.table.caretOffset

    @caret_offset.setter
    def caret_offset(self, value: int) -> None:
        """Sets the ``caretOffset`` field of the ``hhea`` table."""
        self.table.caretOffset = value

    @property
    def metric_data_format(self) -> int:
        """
        A read-only property for the ``metricDataFormat`` field of the ``hhea`` table.

        :return: The ``metricDataFormat`` value.
        :rtype: int
        """
        return self.table.metricDataFormat

    @property
    def number_of_hmetrics(self) -> int:
        """
        A read-only property for the ``numberOfHMetrics`` field of the ``hhea`` table.

        :return: The ``numberOfHMetrics`` value.
        :rtype: int
        """
        return self.table.numberOfHMetrics

    @property
    def run_rise_angle(self) -> float:
        """
        Calculate the slope angle by dividing the caret slope run by the caret slope rise.

        :return: The slope angle in degrees.
        :rtype: float
        """
        rise = self.table.caretSlopeRise
        run = self.table.caretSlopeRun
        run_rise_angle = math.degrees(math.atan(-run / rise))
        return run_rise_angle

    def calc_caret_slope_rise(self, italic_angle: Optional[Union[int, float]] = None) -> int:
        """
        Calculate the ``caretSlopeRise`` field of the ``hhea`` table.

        :param italic_angle: The italic to use for the calculation.
            If ``None``, the italic angle from the ``post`` table will be used.
        :type italic_angle: Optional[Union[int, float]]
        :return: The caret slope rise value.
        :rtype: int
        """

        if italic_angle is None:
            italic_angle = self.ttfont[T_POST].italicAngle

        if italic_angle == 0:
            return 1
        return self.ttfont[T_HEAD].unitsPerEm

    def calc_caret_slope_run(self, italic_angle: Optional[Union[int, float]] = None) -> int:
        """
        Calculate the ``caretSlopeRun`` field of the ``hhea`` table.

        :param italic_angle: The italic to use for the calculation. If ``None``, the italic angle
            from the ``post`` table will be used.
        :type italic_angle: Optional[Union[int, float]]
        :return: The caret slope run value.
        :rtype: int
        """

        if italic_angle is None:
            italic_angle = self.ttfont[T_POST].italicAngle

        if italic_angle == 0:
            return 0
        return otRound(
            math.tan(math.radians(-self.ttfont[T_POST].italicAngle))
            * self.ttfont[T_HEAD].unitsPerEm
        )
