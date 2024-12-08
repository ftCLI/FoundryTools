import logging

from fontTools.ttLib.tables._f_v_a_r import NamedInstance

from foundrytools import Font
from foundrytools.constants import T_STAT

logger = logging.getLogger(__name__)


class UpdateNameTableError(Exception):
    """Raised if the name table cannot be updated when creating a static instance."""


class BadInstanceError(Exception):
    """Raised if the instance is invalid."""


def check_update_name_table(variable_font: Font) -> None:
    """
    Check if the name table can be updated and create a static instance of the variable font.

    This function verifies the presence of the 'STAT' table and its Axis Values, as well as the
    named instances in the 'fvar' table. If these conditions are met, it attempts to create a static
    instance of the variable font with updated font names.

    :param variable_font: The variable font to check and update.
    :type variable_font: Font
    :raises UpdateNameTableError: If the 'STAT' table, Axis Values, or named instances are missing,
        or if an error occurs during the creation of the static instance.
    """
    if T_STAT not in variable_font.ttfont:
        raise UpdateNameTableError("There is no 'STAT' table.")

    stat_table = variable_font.ttfont[T_STAT].table
    if not stat_table.AxisValueArray:
        raise UpdateNameTableError("There are no Axis Values in the 'STAT' table.")

    instances = variable_font.fvar.table.instances
    if not instances:
        raise UpdateNameTableError("There are no named instances in the 'fvar' table.")

    try:
        variable_font.to_static(
            instance=instances[0],
            update_font_names=True,
        )
    except Exception as e:
        raise UpdateNameTableError(str(e)) from e


def check_instance_axes(variable_font: Font, instance: NamedInstance) -> None:
    """
    Check if the instance axes are valid.

    :param variable_font: The variable font.
    :type variable_font: Font
    :param instance: The named instance.
    :type instance: NamedInstance
    :raises KeyError: If the instance axes are invalid.
    """
    axes = variable_font.fvar.get_axes_tags()
    if sorted(instance.coordinates.keys()) != sorted(axes):
        raise BadInstanceError(
            f"Invalid axes: {instance.coordinates.keys()}: " f"valid axes are: {axes}"
        )


def check_instance_coordinates(variable_font: Font, instance: NamedInstance) -> None:
    """
    Check if the instance coordinates are within the axis limits of the variable font.

    :param variable_font: The variable font.
    :type variable_font: Font
    :param instance: The named instance.
    :type instance: NamedInstance
    :raises ValueError: If the instance coordinates are outside the axis limits.
    """
    for axis, value in instance.coordinates.items():
        axis_min, axis_max = variable_font.fvar.get_axis_limits(axis)
        if not axis_min <= value <= axis_max:
            raise BadInstanceError(
                f"Instance coordinates are outside the axis limits: {axis}={value} "
                f"allowed range is {axis_min} to {axis_max}"
            )


def preprocess_instance(var_font: Font, instance: NamedInstance) -> None:
    """
    Preprocess the named instance to ensure that it has a valid postscriptNameID and subfamilyNameID
    even if it is not a named instance in the variable font.

    :param var_font: The variable font.
    :type var_font: Font
    :param instance: The named instance.
    :type instance: NamedInstance
    :return: The preprocessed named instance.
    :rtype: NamedInstance
    """

    named_instances = var_font.fvar.get_instances()
    for i in named_instances:
        print (i.__dict__)
        if i.coordinates == instance.coordinates:
            # Check if the named instance has a valid postscriptNameID and subfamilyNameID
            instance.postscriptNameID = i.postscriptNameID if i.postscriptNameID < 65535 else None
            instance.subfamilyNameID = i.subfamilyNameID if i.subfamilyNameID > 0 else None
            break
        else:
            instance.postscriptNameID = var_font.name.table.addName("")
            instance.subfamilyNameID = var_font.name.table.addName("")

        family_name = str(var_font.name.table.getBestFamilyName())  # cast to string to handle None
        subfamily_name = var_font.name.table.getDebugName(instance.subfamilyNameID)
        postscript_name = var_font.name.table.getDebugName(instance.postscriptNameID)

        if subfamily_name in (None, ""):
            subfamily_name = "_".join(
                [f"{k}_{v}" for k, v in instance.coordinates.items()]
            )
            var_font.name.set_name(instance.subfamilyNameID, subfamily_name)
        else:
            # cast to string to handle None
            subfamily_name = str(var_font.name.table.getDebugName(instance.subfamilyNameID))

        if postscript_name in (None, ""):
            postscript_name = f"{family_name}-{subfamily_name}".replace(" ", "")
            var_font.name.set_name(instance.postscriptNameID, postscript_name)


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


def run(font: Font, instances: list[NamedInstance], update_font_names: bool = True) -> bool:
    if not font.is_variable:
        logger.error("The font is not a variable font.")
        return False

    if instances:
        requested_instances = set(instances)  # Ensure that instances are unique
    else:
        requested_instances = set(font.fvar.get_instances())

    if update_font_names:
        try:
            check_update_name_table(font)
        except UpdateNameTableError as e:
            logger.warning(f"The name table cannot be updated: {e}")
            update_font_names = False

    for instance in requested_instances:
        preprocess_instance(font, instance)
        try:
            check_instance_axes(font, instance)
            check_instance_coordinates(font, instance)
        except BadInstanceError as e:
            logger.warning(f"Invalid instance: {e}")
            continue

        if instance in font.fvar.get_instances():
            static_font = Font(font.to_static(instance, update_font_names))
        else:
            static_font = Font(font.to_static(instance, False))

        cleanup_static_font(static_font)

        file_name = font.name.table.getDebugName(instance.postscriptNameID)
        print(f"Exporting static font: {file_name}")

    return True
