from adl.core.registries import Plugin


class PluginNamePlugin(Plugin):
    type = "adl_vaisala_sc_ftp_decoder"
    label = "ADL Vaisala SC FTP Decoder"

    def get_urls(self):
        return []

    def get_data(self):
        return []
