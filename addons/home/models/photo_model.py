from odoo import models, fields


class PhotoModel(models.Model):
    _name = 'photo.model'
    _description = 'Photo Model'
    _rec_name = 'test'

    photo_field = fields.Binary(string="Photo")
    test = fields.Char(string='test', default='.')
