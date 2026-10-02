import logging

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.G_S_U_B_ import table_G_S_U_B_

from foundrytools.constants import T_GSUB
from foundrytools.core.tables.default import DefaultTbl

logger = logging.getLogger(__name__)


class GsubTable(DefaultTbl):  # pylint: disable=too-few-public-methods
    """This class extends the fontTools ``GSUB`` table."""

    def __init__(self, ttfont: TTFont) -> None:
        """
        Initializes the ``GSUB`` table handler.

        :param ttfont: The ``TTFont`` object.
        :type ttfont: TTFont
        """
        super().__init__(ttfont=ttfont, table_tag=T_GSUB)

    @property
    def table(self) -> table_G_S_U_B_:
        """
        The wrapped ``table_G_S_U_B_`` table object.
        """
        return self._table

    @table.setter
    def table(self, value: table_G_S_U_B_) -> None:
        """
        Wraps a new ``table_G_S_U_B_`` object.
        """
        self._table = value

    def get_feature_tags(self) -> set[str]:
        """
        Returns a list of all the feature tags in the font's GSUB table.

        :return: The feature tags.
        :rtype: list[str]
        """
        return {record.FeatureTag for record in self.table.table.FeatureList.FeatureRecord}

    def get_ui_name_ids(self) -> set[int]:
        """
        Returns a set of all the UI name IDs in the font's GSUB table.

        :return: The UI name IDs.
        :rtype: set[int]
        """
        return {
            record.Feature.FeatureParams.UINameID
            for record in self.table.table.FeatureList.FeatureRecord
            if record.Feature.FeatureParams and hasattr(record.Feature.FeatureParams, "UINameID")
        }

    def remap_ui_name_ids(self, name_ids_map: dict[int, int]) -> None:
        """
        Remap the UI name IDs in the GSUB table.

        :param name_ids_map: A dictionary with the old and new UI name IDs.
        :type name_ids_map: dict[int, int]
        """
        for record in self.table.table.FeatureList.FeatureRecord:
            if record.Feature.FeatureParams and hasattr(record.Feature.FeatureParams, "UINameID"):
                record.Feature.FeatureParams.UINameID = name_ids_map.get(
                    record.Feature.FeatureParams.UINameID, record.Feature.FeatureParams.UINameID
                )

    def rename_feature(self, feature_tag: str, new_feature_tag: str) -> bool:
        """
        Rename a GSUB feature.

        :Example:

        >>> from foundrytools import Font
        >>> font = Font("path/to/font.ttf")
        >>> font.t_gsub.rename_feature("smcp", "ss20")
        >>> font.save("path/to/font.ttf")

        :param feature_tag: The feature tag to rename.
        :type feature_tag: str
        :param new_feature_tag: The new feature tag.
        :type new_feature_tag: str
        :return: True if the feature was renamed, False otherwise.
        :rtype: bool
        """
        if feature_tag == new_feature_tag:
            logger.warning("Old and new feature tags are the same. No changes made.")
            return False

        if new_feature_tag in self.get_feature_tags():
            logger.warning(f"Feature tag '{new_feature_tag}' already exists. No changes made.")
            return False

        modified = False
        if hasattr(self.table.table, "FeatureList"):
            for feature_record in self.table.table.FeatureList.FeatureRecord:
                if feature_record.FeatureTag == feature_tag:
                    feature_record.FeatureTag = new_feature_tag
                    modified = True

            # Sort the feature records by tag. OTS warns if they are not sorted.
            self.sort_feature_records()

        return modified

    def sort_feature_records(self) -> None:
        """Sorts the feature records in the GSUB table by tag."""
        if hasattr(self.table.table, "FeatureList"):
            self.table.table.FeatureList.FeatureRecord.sort(key=lambda x: x.FeatureTag)
