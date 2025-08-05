import logging

import pandas as pd
from adl_ftp_plugin.registries import FTPDecoder
from django.utils import timezone as dj_timezone

logger = logging.getLogger(__name__)


class VaisalaAvimetSCDecoder(FTPDecoder):
    type = "vaisala_avimet_sc"
    compat_type = "vaisala_avimet_sc"
    display_name = "Vaisala Avimet FTP Decoder - Seychelles"
    
    def get_matching_files(self, station_link, files):
        # get all the initial matching files
        matching_files = super().get_matching_files(station_link, files)
        
        if station_link.start_date:
            return matching_files
        
        # sample file name CLIMSOFT_MSG_10.his. Here 10 is the day of the month
        # we only want the files that contain the date of today in the name
        zero_padded_day_today = [f"{dj_timezone.now().day:02}"]
        matching_files = [file for file in matching_files if any(date in file for date in zero_padded_day_today)]
        
        return matching_files
    
    def decode(self, file_path):
        """
        This method decodes the Vaisala Avimet.
        
        :param file_path: The path to the file to decode.
        :return: A dictionary containing the decoded data.
        """
        
        # sample file
        # History file
        # TIMESTAMP	TEMP 1MIN (°C)	TEMPMAX 24H (°C)	TEMPMIN 24H (°C)	RH 1MIN (%)	DP 1MIN (°C)	WS 1MIN (MPS)	WD 1MIN (°)	WS 2MIN (MPS)	WD 2MIN (°)	WS 10MIN (MPS)	WD 10MIN (°)	WSMAX 1MIN (MPS)	WDMAX 1MIN (°)	WSMAX 10MIN (MPS)	WDMAX 10MIN (°)	WSMAX 60MIN (MPS)	WDMAX 60MIN (°)	RAIN 1MIN (MM)	PRESS 1MIN (HPA)	QNH 1MIN (HPA)	QFF 1MIN (HPA)	QFE 1MIN (HPA)	QFE DIFF 3H (HPA)	MESSAGE TO CLIMSOFT
        # 09/04/2025 00:17	27.5	31.0	26.4	88.0	25.4	1.3	226	1.3	220	1.2	214	1.5	244	1.6	244	1.6	258	0.0	1011.4	1011.8	1011.7	1011.4	-0.7	09/04/2025
        #
        
        df = pd.read_csv(file_path, skiprows=1, sep="\t", dtype={"TIMESTAMP": str})
        
        non_data_val_cols = ["TIMESTAMP"]
        
        # convert data columns to float. Errors are coerced to NaN
        for column in df.columns:
            if column not in non_data_val_cols:
                df[column] = pd.to_numeric(df[column], errors='coerce')
        
        df["observation_time"] = pd.to_datetime(df["TIMESTAMP"], format="%d/%m/%Y %H:%M")
        
        # convert the dataframe to a list of dictionaries
        records = df.to_dict(orient="records", )
        
        return {
            "values": records
        }
