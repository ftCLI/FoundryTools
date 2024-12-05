from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.G_S_U_B_ import table_G_S_U_B_

from foundrytools.constants import T_GSUB
from foundrytools.core.tables.default import DefaultTbl


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
        Returns the ``GSUB`` table object.

        :return: The ``GSUB`` table object.
        :rtype: table_G_S_U_B_
        """
        return self._table

    @table.setter
    def table(self, value: table_G_S_U_B_) -> None:
        """
        Sets the ``GSUB`` table object.

        :param value: The ``GSUB`` table object.
        :type value: table_G_S_U_B_
        """
        self._table = value

    def get_ui_name_ids(self) -> set[int]:
        """
        Returns a set of all the UI name IDs in the font's GSUB table

        :return: The UI name IDs.
        :rtype: set[int]
        """
        return {
            record.Feature.FeatureParams.UINameID
            for record in self.table.table.FeatureList.FeatureRecord
            if record.Feature.FeatureParams and hasattr(record.Feature.FeatureParams, "UINameID")
        }

    def rename_feature(self, feature_tag: str, new_feature_tag: str) -> bool:
        """
        Rename a GSUB feature.

        :Example:

        >>> from foundrytools import Font
        >>> font = Font("path/to/font.ttf")
        >>> font.gsub.rename_feature("smcp", "ss20")
        >>> font.save("path/to/font.ttf")

        :param feature_tag: The feature tag to rename.
        :type feature_tag: str
        :param new_feature_tag: The new feature tag.
        :type new_feature_tag: str
        """
        if hasattr(self.table.table, "FeatureList"):
            for feature_record in self.table.table.FeatureList.FeatureRecord:
                if feature_record.FeatureTag == feature_tag:
                    if feature_tag == new_feature_tag:
                        continue
                    feature_record.FeatureTag = new_feature_tag

            # Sort the feature records by tag. OTS warns if they are not sorted.
            self.table.table.FeatureList.FeatureRecord.sort(key=lambda x: x.FeatureTag)

            return True

        return False
