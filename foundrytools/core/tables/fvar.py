from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._f_v_a_r import NamedInstance, table__f_v_a_r

from foundrytools.constants import T_FVAR, T_NAME
from foundrytools.core.tables.default import DefaultTbl


class BadInstanceError(Exception):
    """Raised if the instance is invalid."""


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

    def check_instance_axes(self, instance: NamedInstance) -> None:
        """
        Check if a NamedInstance has valid axes for the font.

        :param instance: The named instance.
        :type instance: NamedInstance
        :raises BadInstanceError: If the instance axes are invalid.
        """
        if sorted(instance.coordinates.keys()) != sorted(self.get_axes_tags()):
            raise BadInstanceError(
                f"Instance axes ({sorted(instance.coordinates.keys())}) do not match the font axes "
                f"({sorted(self.get_axes_tags())})."
            )

    def check_instance_coordinates(self, instance: NamedInstance) -> None:
        """
        Check a NamedInstance's coordinates against the font's axis limits.

        :param instance: The named instance.
        :type instance: NamedInstance
        :raises BadInstanceError: If the instance coordinates are invalid.
        """
        for axis, value in instance.coordinates.items():
            if not self.get_axis_limits(axis)[0] <= value <= self.get_axis_limits(axis)[1]:
                raise BadInstanceError(
                    f"Invalid value for axis '{axis}': {value}"
                    f" (allowed range: {self.get_axis_limits(axis)[0]} to "
                    f"{self.get_axis_limits(axis)[1]})"
                )

    def get_axes_tags(self) -> list[str]:
        """
        Returns the axis tags of the font.

        :return: The axis tags of the font.
        :rtype: list
        """
        return [axis.axisTag for axis in self.table.axes]

    def get_axis_limits(self, axis_tag: str) -> tuple[float, float]:
        """
        Returns the minimum and maximum values of an axis.

        :param axis_tag: The axis tag.
        :type axis_tag: str
        :return: The limits of the axis.
        :rtype: tuple[float, float]
        """
        # Set 'hidden' to True because we don't know if the axis tag belongs to a hidden axis
        for axis in self.table.axes:
            if axis.axisTag == axis_tag:
                return axis.minValue, axis.maxValue

        raise ValueError(f"Axis '{axis_tag}' not found.")

    @staticmethod
    def get_fallback_subfamily_name(instance: NamedInstance) -> str:
        """
        Get the fallback subfamily name for a NamedInstance object.

        :param instance: The NamedInstance object.
        :type instance: NamedInstance
        :return: The fallback subfamily name.
        :rtype: str
        """
        return "_".join([f"{k}_{v}" for k, v in instance.coordinates.items()])

    def get_fallback_postscript_name(self, instance: NamedInstance) -> str:
        """
        Get the fallback PostScript name for a NamedInstance object.

        :param instance: The NamedInstance object.
        :type instance: NamedInstance
        :return: The fallback PostScript name.
        :rtype: str
        """
        family_name = str(self.ttfont[T_NAME].getBestFamilyName())  # cast to str to handle None
        subfamily_name = self.get_fallback_subfamily_name(instance)
        return f"{family_name}-{subfamily_name}".replace(" ", "").replace(".", "_")

    def get_instance_postscript_name(self, instance: NamedInstance) -> str:
        """
        Get the PostScript name of a NamedInstance object.

        :param instance: The NamedInstance object.
        :type instance: NamedInstance
        :return: The PostScript name.
        :rtype: str
        """
        if instance.postscriptNameID < 65535:
            postscript_name = self.ttfont[T_NAME].getDebugName(instance.postscriptNameID)
            if postscript_name:
                return postscript_name
        return self.get_fallback_postscript_name(instance)

    def get_named_or_custom_instance(self, instance: NamedInstance) -> tuple[bool, NamedInstance]:
        """
        Returns a named instance if the instance coordinates are the same, otherwise the custom
        instance.

        :param instance: The named instance.
        :type instance: NamedInstance
        :return: A tuple with a boolean indicating if the instance is named and the instance object.
        :rtype: tuple[bool, NamedInstance]
        """
        for named_instance in self.table.instances:
            if named_instance.coordinates == instance.coordinates:
                return True, named_instance

        return False, instance
