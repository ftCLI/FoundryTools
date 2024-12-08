from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._f_v_a_r import Axis, NamedInstance, table__f_v_a_r

from foundrytools.constants import T_FVAR
from foundrytools.core.tables.default import DefaultTbl


class FvarTable(DefaultTbl):  # pylint: disable=too-few-public-methods
    """This class extends the fontTools ``fvar`` table."""

    def __init__(self, ttfont: TTFont) -> None:
        """
        Initializes the ``kern`` table handler.

        :param ttfont: The ``TTFont`` object
        :type ttfont: TTFont
        """
        super().__init__(ttfont=ttfont, table_tag=T_FVAR)

    @property
    def table(self) -> table__f_v_a_r:
        """
        Returns the ``kern`` table object.

        :return: The ``kern`` table object.
        :rtype: table__k_e_r_n
        """
        return self._table

    @table.setter
    def table(self, value: table__f_v_a_r) -> None:
        """
        Sets the ``kern`` table object.

        :param value: The ``kern`` table object.
        :type value: table__k_e_r_n
        """
        self._table = value

    def get_axes(self, hidden: bool = False) -> list[Axis]:
        """
        Returns the variable axes.

        :param hidden: Whether to include hidden axes.
        :type hidden: bool
        :return: The axes of the font.
        :rtype: list[Axis]
        """
        if hidden:
            return self.table.axes
        return [axis for axis in self.table.axes if not axis.flags & 0x0001]

    def get_axis_limits(self, axis_tag: str) -> tuple[float, float]:
        """
        Returns the minimum and maximum values of an axis.

        :param axis_tag: The axis tag.
        :type axis_tag: str
        :return: The limits of the axis.
        :rtype: tuple[float, float]
        """
        # Set 'hidden' to True because we don't know if the axis tag belongs to a hidden axis
        for axis in self.get_axes(hidden=True):
            if axis.axisTag == axis_tag:
                return axis.minValue, axis.maxValue

        raise ValueError(f"Axis '{axis_tag}' not found.")

    def get_axes_tags(self, hidden: bool = False) -> list[str]:
        """
        Returns the axis tags of the font.

        :return: The axis tags of the font.
        :rtype: list
        """
        return [axis.axisTag for axis in self.get_axes(hidden=hidden)]

    def get_instances(self) -> list[NamedInstance]:
        """
        Returns the named instances of the variable font.

        :return: The instances of the font.
        :rtype: list
        """
        return self.table.instances
