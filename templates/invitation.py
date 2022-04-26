# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, line-too-long, too-few-public-methods
"""Login Email Template"""
from datetime import date
from configparser import ConfigParser
from library.config_parser import config_section_parser
COPYRIGHT_YEAR = str(date.today().year)

class Invitation():
    """Class for Login Invitation"""

    # INITIALIZE
    def __init__(self):
        """The Constructor Invitation class"""
        self.config = ConfigParser()
        # CONFIG FILE
        self.config.read("config/config.cfg")
        # SET CONFIG VALUES
        self.host = config_section_parser(self.config, "HOST")['api']
        self.hostname = config_section_parser(self.config, "HOST")['hostname']

    def message_temp(self, username, password, url):
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
                            <h1 style="font-family:arial,sans-serif;color:#222222;font-weight:bold;font-size:24px;margin:0;padding:0 0 20px 0;text-align:left">Invitation</h1>
                            <p style="font-family:arial,sans-serif;color:#474747;font-weight:normal;font-size:14px;margin:0;padding:0 0 0 0;text-align:left;line-height:1.5">By clicking in the URL, you will redirect to login page:<br><a style="word-break:break-word" href='"""+str(url)+"""' target="_blank" data-saferedirecturl='"""+str(url)+"""'>"""+str(url)+"""</a></p>
                            <p style="font-family:arial,sans-serif;color:#474747;font-weight:normal;font-size:14px;margin:0;padding:0 0 0 0;text-align:left;line-height:1.5"><br>Use the following details for your temporary login:</p>
                            <p style="background:#e1e1e1;padding:10px;border-radius:2px;color:#222222;font-size:14px;">
                            <strong>Username:</strong> """+ username+""" <br>
                            <strong>Password:</strong> """ + password+ """
                            </p>
                            <p style="font-family:arial,sans-serif;color:#474747;font-weight:normal;font-size:14px;margin:0;padding:0 0 0 0;text-align:left;line-height:1.5">If you have any questions, feel free to email us. We are always happy to help out.</p>
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
