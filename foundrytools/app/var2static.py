import logging
from typing import Optional

from fontTools.ttLib.tables._f_v_a_r import NamedInstance

from foundrytools import Font

logger = logging.getLogger(__name__)


class Var2StaticError(Exception):
    """Raised when an error occurs during the conversion of a variable font to a static font."""


class UpdateNameTableError(Exception):
    """Raised if the name table cannot be updated when creating a static instance."""


def check_update_name_table(var_font: Font) -> None:
    """
    Check if the name table can be updated when creating a static instance.

    :param var_font: The variable font to check and update.
    :type var_font: Font
    :raises UpdateNameTableError: If the 'STAT' table, Axis Values, or named instances are missing,
        or if an error occurs during the creation of the static instance.
    """
    try:
        var_font.to_static(instance=var_font.fvar.table.instances[0], update_font_names=True)
    except Exception as e:
        raise UpdateNameTableError(str(e)) from e


def cleanup_static_font(static_font: Font) -> None:
    """
    Clean up the static font by removing unnecessary tables and data.

    :param static_font: The static font to clean up.
    :type static_font: Font
    """
    tables_to_remove = ["cvar", "STAT"]
    for table_tag in tables_to_remove:
        if table_tag in static_font.ttfont:
            del static_font.ttfont[table_tag]

    static_font.name.remove_names(name_ids=[25])
    static_font.name.remove_unused_names()


def update_name_table(var_font: Font, static_font: Font, instance: NamedInstance) -> None:
    """
    Update the name table of the static font.

    :param var_font: The variable font.
    :type var_font: Font
    :param static_font: The static font.
    :type static_font: Font
    :param instance: The named instance.
    :type instance: NamedInstance
    """
    family_name = var_font.name.get_best_family_name()
    subfamily_name = var_font.fvar.get_fallback_subfamily_name(instance)

    static_font.name.set_name(1, f"{family_name} {subfamily_name}")
    static_font.name.set_name(16, family_name)
    static_font.name.set_name(17, subfamily_name)
    static_font.name.build_postscript_name()
    static_font.name.build_full_font_name()
    static_font.name.build_unique_identifier()


def run(
    var_font: Font, instance: NamedInstance, update_font_names: bool = True
) -> Optional[tuple[Font, str]]:
    """
    Convert a variable font to a static font.

    :param var_font: The variable font to convert.
    :type var_font: Font
    :param instance: The named instance to use.
    :type instance: NamedInstance
    :param update_font_names: Whether to update the font names in the name table. Defaults to True.
    :type update_font_names: bool
    :return: The static font and the file stem.
    :rtype: Optional[tuple[Font, str]]
    """

    if not var_font.is_variable:
        logger.error("The font is not a variable font.")
        return None

    # If the instance coordinates are the same as an existing named instance, we use the
    # existing instance instead of the original one. This allows to access the instance
    # postscriptNameID and subfamilyNameID and to update the name table.
    is_named_instance, instance = var_font.fvar.get_named_or_custom_instance(instance)

    try:
        if is_named_instance:
            static_font = Font(var_font.to_static(instance, update_font_names))
        else:
            static_font = Font(var_font.to_static(instance, False))

        cleanup_static_font(static_font)
        if not is_named_instance or not update_font_names:
            update_name_table(var_font, static_font, instance)

        file_stem = var_font.fvar.get_instance_postscript_name(instance)

        return static_font, file_stem

    except Exception as e:
        raise Var2StaticError(str(e)) from e
