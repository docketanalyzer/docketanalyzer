import os
import time
import requests
from docketanalyzer.utils import PACER_USERNAME, PACER_PASSWORD


class JuriscraperUtility:
    def __init__(
        self, host='http://localhost', port=4444,
        pacer_username=PACER_USERNAME, pacer_password=PACER_PASSWORD,
    ):
        self.host = host
        self.port = port
        self.pacer_username = pacer_username
        self.pacer_password = pacer_password
        self.cache = {}

    @property
    def url(self):
        return f'{self.host}:{self.port}/wd/hub/'

    @property
    def is_running(self):
        try:
            requests.get(self.url)
            return True
        except requests.exceptions.ConnectionError:
            return False

    @property
    def session(self):
        if 'session' not in self.cache:
            from juriscraper.pacer import PacerSession

            os.environ['WEBDRIVER_CONN'] = self.host
            if self.is_running:
                print('Selenium server already running.')
            else:
                cmd = f'docker run -d -p {self.port}:4444 selenium/standalone-firefox-debug'
                print(f'Starting Selenium server with command: {cmd}')
                os.system(cmd)
                while not self.is_running:
                    print('waiting for service to start...')
                    time.sleep(3)
            self.cache['session'] = PacerSession(username=self.pacer_username, password=self.pacer_password)
        return self.cache['session']

    def find_candidates(self, docket_id):
        from juriscraper.pacer import PossibleCaseNumberApi
        from juriscraper.lib.string_utils import force_unicode

        court, docket_number = docket_id.split('__')
        docket_number = docket_number.replace('_', ':')
        case_numbers = PossibleCaseNumberApi(court, self.session)
        case_numbers.query(docket_number)
        return [{
            "docket_number": force_unicode(node.xpath("./@number")[0]),
            "pacer_case_id": force_unicode(node.xpath("./@id")[0]),
            "title": force_unicode(node.xpath("./@title")[0]),
        } for node in case_numbers.tree.xpath("//case")]

    def purchase_docket(self, docket_id, **kwargs):
        court, _ = docket_id.split('__')
        pacer_case_id = self.find_candidates(docket_id)[0]['pacer_case_id']
        return self.purchase_docket_with_pacer_case_id(court, pacer_case_id, **kwargs)

    def purchase_docket_with_pacer_case_id(self, court, pacer_case_id, **kwargs):
        from juriscraper.pacer import DocketReport

        docket_report = DocketReport(court, self.session)
        docket_report.query(pacer_case_id, **kwargs)
        docket_html = docket_report.response.text
        return docket_html, docket_report.data

    def parse(self, docket_html, court):
        from juriscraper.pacer import DocketReport

        parser = DocketReport(court)
        # temp fix for error string issue https://github.com/freelawproject/juriscraper/issues/1025
        if 'This case was administratively closed' in parser.ERROR_STRINGS:
            parser.ERROR_STRINGS.remove('This case was administratively closed')
        parser._parse_text(docket_html)
        return parser.data

    def purchase_document(self, pacer_case_id, pacer_doc_id, court):
        from juriscraper.pacer import DocketReport

        if pacer_doc_id is None:
            return {'file': None, 'status': 'no pacer_doc_id provided'}

        docket_report = DocketReport(court, self.session)
        r, status = docket_report.download_pdf(pacer_case_id, pacer_doc_id)
        pdf = r.content if r else None
        return {'file': pdf, 'status': 'success' if not status else status}

    def purchase_attachment(self, pacer_case_id, pacer_doc_id, attachment_number, court):
        from juriscraper.pacer import AttachmentPage

        attachments = AttachmentPage(court, self.session)
        attachments.query(pacer_doc_id)
        attachments = attachments.data['attachments']
        for attachment in attachments:
            if int(attachment['attachment_number']) == int(attachment_number):
                return self.purchase_document(pacer_case_id, attachment['pacer_doc_id'], court)
        return {'status': 'error', 'file': None}