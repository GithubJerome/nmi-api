# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, line-too-long, too-few-public-methods
"""Update Email Template"""
from datetime import date
from configparser import ConfigParser
from library.config_parser import config_section_parser
COPYRIGHT_YEAR = str(date.today().year)

class EmailUpdate():
    """Class for EmailUpdate"""

    # INITIALIZE
    def __init__(self):
        """The Constructor EmailUpdate class"""
        self.config = ConfigParser()
        # CONFIG FILE
        self.config.read("config/config.cfg")
        # SET CONFIG VALUES
        self.host = config_section_parser(self.config, "HOST")['api']
        self.hostname = config_section_parser(self.config, "HOST")['hostname']

    def message_temp(self, username, old_email, new_email):
        """Message Temporary"""
        img_url = "{0}/images/nmi_logo.png".format(self.host)
        email_temp = """
            <div style="background:#fcfcfc;font-family:arial,sans-serif;color:#474747;padding:2%">
                <table style="width:100%;max-width:600px;border:1px solid #dbdbdb;border-radius:5px;background:#fff;padding:0px;margin:0 auto 0px auto" border="0" cellspacing="0" cellpadding="0">
                    <tbody>
                        <tr>
                            <td style="padding:5px 30px 5px 30px;background:#7AC2AF;color:#fff;font-size:16px;text-align:left;font-weight:bold;border-radius:3px 3px 0 0;text-decoration:none">&nbsp;</td>
                        </tr>
                        <tr>
                            <td style="padding:15px 30px 10px;border-bottom:1px solid #dbdbdb"><a style="text-decoration:none" title="Nederlands Mathematisch Instituut" href="""+self.hostname+""" target="_blank" data-saferedirecturl="""+self.hostname+"""><img style="width:80%;max-width:100%;margin:0 auto;font-weight:bold;color:#222;font-size:38px;text-decoration:none" src="""+ img_url+""" alt="Nederlands Mathematisch Instituut" class="CToWUd"></a></td>
                        </tr>
                        <tr>
                        <td style="padding:30px 30px 30px 30px">
                            <p style="font-family:arial,sans-serif;color:#474747;font-weight:normal;font-size:14px;margin:0;padding:0 0 0 0;text-align:left;line-height:1.5">Hi """+username+""",<br>
                            <br>Your username has been successfully changed from """+old_email+""" to """+new_email+""".</p>

                        </td>
                        </tr>
                    </tbody>
                </table>
                <table style="width:100%;max-width:600px;text-align:left;margin:20px auto 0 auto;font-family:arial,sans-serif;font-size:10px;color:#777777;line-height:1.3" border="0" cellspacing="0" cellpadding="0">
                    <tbody>
                        <tr>
                            <td style="width:100%;text-align:left;padding-bottom:10px">Copyright © <span class="il">Nederlands Mathematisch Instituut</span> """+  COPYRIGHT_YEAR +"""</td>
                        </tr>
                    </tbody>
                </table>
                <div class="yj6qo">
                </div>
                <div class="adL">
                </div>
            </div>
        """
        return email_temp
