from odoo import fields, models, api, exceptions


class CategorieClient(models.Model):
    _name = 'categorie.client'
    _description = 'Categorie client'

    name = fields.Char(string='Catégorie')
    du_pts = fields.Integer(string='Du (pts)')
    au_pts = fields.Integer(string='Au (pts)')
    reduction = fields.Integer(string='Réduction %')
    reduction_pr = fields.Char(string='Reduction %', compute='_compute_pourcentage_display', store=True)
    options_gratuit = fields.Many2many('options', string='Options Gratuites')
    category_code = fields.Char(string='Code', unique=True)


    option_one = fields.Many2one('options', string='Option 1', compute="_compute_options", store=True)
    option_two = fields.Many2one('options', string='Option 2', compute="_compute_options", store=True)
    option_three = fields.Many2one('options', string='Option 3', compute="_compute_options", store=True)
    option_four = fields.Many2one('options', string='Option 4', compute="_compute_options", store=True)
    option_five = fields.Many2one('options', string='Option 5', compute="_compute_options", store=True)
    option_six = fields.Many2one('options', string='Option 6', compute="_compute_options", store=True)
    option_seven = fields.Many2one('options', string='Option 7', compute="_compute_options", store=True)
    option_eight = fields.Many2one('options', string='Option 8', compute="_compute_options", store=True)
    option_nine = fields.Many2one('options', string='Option 9', compute="_compute_options", store=True)
    option_ten = fields.Many2one('options', string='Option 10', compute="_compute_options", store=True)


    @api.depends('reduction')
    def _compute_pourcentage_display(self):
        for record in self:
            record.reduction_pr = "{} %".format(record.reduction)

    @api.constrains('du_pts', 'au_pts')
    def _check_interval_overlap(self):
        for record in self:
            if record.au_pts <= record.du_pts:
                raise exceptions.ValidationError(
                    "Le champ 'Au (pts)' doit être supérieur à 'Du (pts)'."
                )
            overlapping_records = self.env['categorie.client'].search([
                ('id', '!=', record.id),
                ('du_pts', '<=', record.au_pts),
                ('au_pts', '>=', record.du_pts),
            ])
            if overlapping_records:
                raise exceptions.ValidationError(
                    "Les intervalles de points que vous avez saisie chevauchent avec la catégorie '{}' "
                    "[{} - {}]".format(overlapping_records[0].name, overlapping_records[0].du_pts,
                                       overlapping_records[0].au_pts)
                )

    @api.depends('options_gratuit')
    def _compute_options(self):
        for record in self:
            options = record.options_gratuit[:10]  # Prend les 10 premières options
            options_list = options.mapped('id')  # Extrait les IDs des options

            # Assigne les valeurs aux champs Many2one
            record.option_one = options_list[0] if len(options_list) > 0 else False
            record.option_two = options_list[1] if len(options_list) > 1 else False
            record.option_three = options_list[2] if len(options_list) > 2 else False
            record.option_four = options_list[3] if len(options_list) > 3 else False
            record.option_five = options_list[4] if len(options_list) > 4 else False
            record.option_six = options_list[5] if len(options_list) > 5 else False
            record.option_seven = options_list[6] if len(options_list) > 6 else False
            record.option_eight = options_list[7] if len(options_list) > 7 else False
            record.option_nine = options_list[8] if len(options_list) > 8 else False
            record.option_ten = options_list[9] if len(options_list) > 9 else False

