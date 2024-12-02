from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.G_S_U_B_ import table_G_S_U_B_

from foundrytools.constants import T_GSUB
from foundrytools.tables.default import DefaultTbl


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

    def rename_feature(self, feature_tag: str, new_feature_tag: str) -> None:
        """
        Rename a GSUB feature.

        :param feature_tag: The feature tag to rename.
        :type feature_tag: str
        :param new_feature_tag: The new feature tag.
        :type new_feature_tag: str
        """

        if hasattr(self.table, "FeatureList"):
            for feature_record in self.table.FeatureList.FeatureRecord:
                if feature_record.FeatureTag == feature_tag:
                    feature_record.FeatureTag = new_feature_tag
