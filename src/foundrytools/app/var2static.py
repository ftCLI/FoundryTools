"""VAR to static."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from fontTools.varLib.instancer import OverlapMode, instantiateVariableFont

from foundrytools import Font
from foundrytools.constants import T_GSUB, NameIds

if TYPE_CHECKING:
    from fontTools.ttLib.tables._f_v_a_r import Axis, NamedInstance


class Var2StaticError(Exception):
    """Raised when an error occurs during the conversion of a variable font to a static font."""


class UpdateNameTableError(Exception):
    """Raised if the name table cannot be updated when creating a static instance."""


class BadInstanceError(Exception):
    """Raised if the instance is invalid."""


def check_update_name_table(var_font: Font) -> None:
    """
    Check if the name table can be updated when creating a static instance.

    This method should be called once by third-party applications before starting the conversion
    process. Calling it at every iteration is not necessary and slows down the process.

    :param var_font: The variable font to check and update.
    :type var_font: Font
    :raises UpdateNameTableError: If the 'STAT' table, Axis Values, or named instances are missing,
        or if an error occurs during the creation of the static instance.
    """
    try:
        create_static_instance(var_font, var_font.t_fvar.table.instances[0], update_font_names=True)
    except Exception as e:
        raise UpdateNameTableError(str(e)) from e


def check_instance(var_font: Font, instance: NamedInstance) -> None:
    """
    Check if the instance is valid.

    :param var_font: The variable font.
    :type var_font: Font
    :param instance: The named instance.
    :type instance: NamedInstance
    :raises BadInstanceError: If the instance is invalid.
    """
    axes: list[Axis] = var_font.t_fvar.table.axes

    for axis_tag, value in instance.coordinates.items():
        axis_obj = next((a for a in axes if a.axisTag == axis_tag), None)
        if axis_obj is None:
            msg = f"Cannot create static font: '{axis_tag}' not present in fvar"
            raise BadInstanceError(msg)
        if not axis_obj.minValue <= value <= axis_obj.maxValue:
            msg = (
                f"Cannot create static font: '{axis_tag}' out of bounds "
                f"(value: {value} min: {axis_obj.minValue} max: {axis_obj.maxValue})"
            )
            raise BadInstanceError(msg)


def get_existing_instance(var_font: Font, instance: NamedInstance) -> tuple[bool, NamedInstance]:
    """
    Return a named instance if the instance coordinates are the same, otherwise the custom instance.

    :param var_font: The variable font.
    :type var_font: Font
    :param instance: The named instance.
    :type instance: NamedInstance
    :return: A tuple with a boolean indicating if the instance is named and the instance object.
    :rtype: tuple[bool, NamedInstance]
    """
    for existing_instance in var_font.t_fvar.table.instances:
        if existing_instance.coordinates == instance.coordinates:
            return True, existing_instance

    return False, instance


def create_static_instance(var_font: Font, instance: NamedInstance, update_font_names: bool, overlap: int = 1) -> Font:  # noqa: FBT001
    """
    Create a static instance from a variable font.

    :param var_font: The variable font.
    :type var_font: Font
    :param instance: A named instance with axis values.
    :type instance: NamedInstance
    :param update_font_names: If ``True``, update the font names in the static instance.
    :type update_font_names: bool
    :param overlap: The overlap mode. Defaults to 1 (KEEP_AND_SET_FLAGS).
    :type overlap: OverlapMode
    :return: A static instance of the font.
    :rtype: Font
    """
    # We need to cast the overlap mode to the correct type.
    overlap = cast(OverlapMode, overlap)

    return Font(
        instantiateVariableFont(
            var_font.ttfont,
            axisLimits=instance.coordinates,
            inplace=False,
            optimize=True,
            overlap=overlap,
            updateFontNames=update_font_names,
        )
    )


def cleanup_static_font(static_font: Font) -> None:
    """
    Clean up the static font by removing tables left by ``InstantiateVariableFont`` and remapping the name IDs.

    :param static_font: The static font to clean up.
    :type static_font: Font
    """
    tables_to_remove = ["cvar", "STAT"]
    for table_tag in tables_to_remove:
        if table_tag in static_font.ttfont:
            del static_font.ttfont[table_tag]

    static_font.t_name.build_unique_identifier()

    # Remove unnecessary NameRecords and Macintosh-specific NameRecords, and remap the name IDs in
    # the GSUB table.
    static_font.t_name.remove_names(name_ids=[25])
    static_font.t_name.remove_mac_names()
    _remove_unused_names(static_font)  # This is faster than removeUnusedNames.
    name_ids_map = static_font.t_name.remap_name_ids()
    if T_GSUB in static_font.ttfont:
        static_font.t_gsub.remap_ui_name_ids(name_ids_map)


def _remove_unused_names(static_font: Font) -> None:
    """``removeUnusedNames`` is very slow. This should be enough for most cases."""
    if T_GSUB not in static_font.ttfont:
        return
    ui_name_ids = static_font.t_gsub.get_ui_name_ids()
    name_ids_to_remove = [
        name.nameID
        for name in static_font.t_name.table.names
        if name.nameID >= 256 and name.nameID not in ui_name_ids  # noqa: PLR2004
    ]
    static_font.t_name.remove_names(name_ids=name_ids_to_remove)


def update_name_table(var_font: Font, static_font: Font, instance: NamedInstance) -> None:
    """
    Update the name table of the static font.

    In case ``InstantiateVariableFont`` could not update it, or if the instance is non-existing.

    :param var_font: The variable font.
    :type var_font: Font
    :param static_font: The static font.
    :type static_font: Font
    :param instance: The named instance.
    :type instance: NamedInstance
    """
    family_name = var_font.t_name.get_best_family_name()
    subfamily_name = "_".join([f"{k}_{v}" for k, v in instance.coordinates.items()])
    postscript_name = f"{family_name}-{subfamily_name}".replace(" ", "").replace(".", "_")

    # Build the name table of the static font.
    static_font.t_name.set_name(NameIds.FAMILY_NAME, f"{family_name} {subfamily_name}")
    static_font.t_name.set_name(NameIds.POSTSCRIPT_NAME, postscript_name)
    static_font.t_name.set_name(NameIds.TYPO_FAMILY_NAME, family_name)
    static_font.t_name.set_name(NameIds.TYPO_SUBFAMILY_NAME, subfamily_name)
    static_font.t_name.build_full_font_name()


def run(
    var_font: Font,
    instance: NamedInstance,
    *,
    update_font_names: bool = True,
    overlap: int = 1,
) -> tuple[Font, str]:
    """
    Convert a variable font to a static font.

    :param var_font: The variable font to convert.
    :type var_font: Font
    :param instance: The named instance to use.
    :type instance: NamedInstance
    :param update_font_names: Whether to update the font names in the name table. Defaults to True.
    :type update_font_names: bool
    :param overlap: The overlap mode. Defaults to 1 (KEEP_AND_SET_FLAGS).
    :type overlap: int
    :return: The static font and the file stem.
    :rtype: Optional[tuple[Font, str]]
    """
    if not var_font.is_variable:
        msg = "The font is not a variable font."
        raise Var2StaticError(msg)

    try:
        # Checks if the instance has valid axes and coordinates are within the axis limits. If not,
        # raises a BadInstanceError.
        check_instance(var_font, instance)

        # If the instance coordinates are the same as an existing instance, we use the existing
        # instance instead of the original one. This allows to access the instance postscriptNameID
        # and subfamilyNameID and to update the name table.
        is_existing_instance, instance = get_existing_instance(var_font, instance)

        if is_existing_instance:
            static_font = create_static_instance(var_font, instance, update_font_names, overlap)
        else:
            static_font = create_static_instance(var_font, instance, update_font_names=False, overlap=overlap)

        # We update the name table with the instance coordinates if the instance is non-existing or
        # if the name table cannot be updated.
        if not is_existing_instance or not update_font_names:
            update_name_table(var_font, static_font, instance)

        cleanup_static_font(static_font)

        file_name = static_font.t_name.get_debug_name(NameIds.POSTSCRIPT_NAME)
        file_name += static_font.get_file_ext()

    except Exception as e:
        raise Var2StaticError(str(e)) from e

    return static_font, file_name
