from odoo import http
from odoo.http import request

class ModeleController(http.Controller):

    @http.route('/api/modeles', type='json', auth='public', methods=['GET'])
    def list_modeles(self):
        modeles = request.env['modele'].search([])
        result = []
        for modele in modeles:
            attachments = []
            for attachment in modele.photo_ids:
                attachments.append({
                    'id': attachment.id,
                    'name': attachment.name,
                    'datas': attachment.datas.decode('utf-8') if attachment.datas else ''
                })
            result.append({
                'id': modele.id,
                'name': modele.name,
                'photos': attachments
            })
        return result
