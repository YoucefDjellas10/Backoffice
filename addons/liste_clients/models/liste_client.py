from odoo import models, fields, api
from odoo.exceptions import UserError
import random
import string
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)


class ListeClient(models.Model):
    _name = 'liste.client'
    _description = 'liste des clients'

    name = fields.Char(string='Nom complet', compute='_compute_full_name', store=True)
    civilite = fields.Selection([('Mr', 'M.'), ('Mme', 'Mme'), ('Mlle', 'Mlle')], string='Civilité')
    nom = fields.Char(string='Nom', required=True)
    prenom = fields.Char(string='Prénom')
    email = fields.Char(string='Email')
    date_de_naissance = fields.Date(string='Date de naissance')
    mobile = fields.Char(string='Mobile')
    telephone = fields.Char(string='Téléphone')
    risque = fields.Selection([('faible', 'Faible'), ('moyen', 'Moyen'), ('eleve', 'Elevé')], string='Risque',
                              default='faible')
    note = fields.Text(string='Note')
    date_de_permis = fields.Date(string='Date de permis')
    categorie_client = fields.Many2one('categorie.client', string='Categorie',
                                       compute='_compute_categorie_client', store=True)
    category_client_name = fields.Char(string='Category name',related='categorie_client.name', store=True)
    options_gratuit = fields.Many2many('options', string='Options Gratuites',
                                       related='categorie_client.options_gratuit')
    reduction = fields.Integer(string='Réduction %', related='categorie_client.reduction', store=True)

    total_points = fields.Integer(string='Total des points', compute='_compute_total_points', store=True, editable=True)
    total_points_char = fields.Char(string='Total des points', compute='_compute_total_points_char', store=True)
    solde = fields.Monetary(string='Solde non consomé', currency_field='devise', compute='_compute_solde', store=True, editable=True)
    devise = fields.Many2one('res.currency', string='Devise', readonly=True,
                             default=lambda self: self.env.ref('base.EUR').id)
    total_reservation = fields.Monetary(currency_field='devise')
    code_prime = fields.Char(string='Code Prime', store=True, readonly=True)

    parrain = fields.Many2one('liste.client', string='Le parrain')
    filleul = fields.One2many('liste.client', 'parrain', string='Les filleuls')

    solde_total = fields.Integer(string='Solde Total')
    solde_consomer = fields.Integer(string='Solde consomé')

    otp = fields.Char(string='otp')
    otp_created_at = fields.Datetime(string='otp created at')
    otp_attempts = fields.Integer(string='opt attempts', default=0)


    create_date = fields.Datetime()


    @api.model
    def _generate_code_prime(self):
        domain = [
            ('code_prime', '=like', '01%'),  # code_prime commence par "01"
            ('categorie_client.name', '!=', 'DRIVER')  # catégorie différente de "DRIVER"
        ]
        all_ids = self.env['liste.client'].search(domain).ids
        for i in range(0, len(all_ids), 700):
            batch_ids = all_ids[i:i + 700]
            for record in self.env['liste.client'].browse(batch_ids):
                prefix = "01"
                if record.categorie_client:
                    name = record.categorie_client.name
                    prefix = {"ESSENTIEL": "02", "EXCELLENT": "03", "VIP": "04"}.get(name, "01")
                year_suffix = str(datetime.now().year)[-2:]
                random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                record.code_prime = f"{prefix}{year_suffix}{random_part}"



    @api.depends('solde_total', 'solde_consomer')
    def _compute_solde(self):
        for record in self:
            record.solde = record.solde_total - record.solde_consomer if record.solde_total else 0

    def action_ajouter_filleul_direct(self):
        return {
            'name': 'Ajouter un Filleul',
            'type': 'ir.actions.act_window',
            'res_model': 'liste.client',
            'view_mode': 'form',
            'target': 'new',
            'view_id': self.env.ref('liste_clients.view_filleul_form_popup').id,
            'context': {'default_parrain': self.id},
        }

    def action_save(self):
        solde_parrainage_record = self.env['solde.parrainage'].search([], limit=1)
        if not solde_parrainage_record:
            raise UserError("Aucun enregistrement trouvé dans Solde Parrainage.")
        self.solde_total += solde_parrainage_record.parrain_solde
        new_filleul_id = self.env.context.get('active_id')
        new_filleul = self.env['liste.client'].browse(new_filleul_id)
        if not new_filleul:
            raise UserError("Aucun enregistrement filleul n'a été trouvé.")
        new_filleul.solde_total += solde_parrainage_record.filleul_solde
        return {'type': 'ir.actions.act_window_close'}

    @api.depends('total_points')
    def _compute_categorie_client(self):
        for record in self:
            categorie = self.env['categorie.client'].search([
                ('du_pts', '<=', record.total_points),
                ('au_pts', '>=', record.total_points)
            ], limit=1)

            record.categorie_client = categorie.id if categorie else False

    @api.depends('total_reservation')
    def _compute_total_points(self):
        for record in self:
            record.total_points = int(record.total_reservation)

    @api.depends('civilite', 'nom', 'prenom')
    def _compute_full_name(self):
        for record in self:
            # Concatenate civilite, nom, and prenom with spaces
            record.name = ' '.join(filter(None, [record.civilite, record.nom, record.prenom]))

    def action_send_welcome_email(self):
        template_id = self.env.ref('liste_clients.email_template_welcome_client').id
        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)
            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def action_enregistrement_email(self):
        template_id = self.env.ref('liste_clients.template_enregistrement_compte_client').id
        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)
            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def action_newslatter_email(self):
        template_id = self.env.ref('liste_clients.template_newslatter_client').id
        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)
            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    def action_driver_email(self):
        template_id = self.env.ref('liste_clients.template_driver_client_finale_template_').id
        for record in self:
            if not record.email:
                raise UserError("L'adresse email est manquante pour %s" % record.name)
            template = self.env['mail.template'].browse(template_id)
            if template:
                template.send_mail(record.id, force_send=True)
            else:
                raise UserError("Modèle de courrier introuvable ou invalide.")

    @api.depends('total_points')
    def _compute_total_points_char(self):
        for record in self:
            record.total_points_char = f"{record.total_points} pts"


    def action_normaliser_noms_prenoms(self):
        tous_les_clients = self.env['liste.client'].search([])
        compteur = 0

        for client in tous_les_clients:
            modifie = False
            if client.nom:
                nom_normalise = client.nom.strip().upper()
                if client.nom != nom_normalise:
                    client.nom = nom_normalise
                    modifie = True

            if client.prenom:
                prenom_normalise = client.prenom.strip().upper()
                if client.prenom != prenom_normalise:
                    client.prenom = prenom_normalise
                    modifie = True

            if modifie:
                compteur += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Normalisation terminée',
                'message': f'{compteur} client(s) ont été mis à jour avec succès.',
                'type': 'success',
                'sticky': False,
            }
        }


    def action_supprimer_doublons(self):
        """
        Lance la suppression des doublons en arrière-plan
        """
        # Lancer le traitement en arrière-plan
        self.env.ref('liste_clients.cron_supprimer_doublons').method_direct_trigger()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Traitement lancé',
                'message': 'La suppression des doublons a été lancée en arrière-plan. '
                           'Vous serez notifié par email quand le traitement sera terminé.',
                'type': 'info',
                'sticky': True,
            }
        }

    def cron_supprimer_doublons(self):
        """
        Méthode appelée par le cron pour supprimer les doublons
        Traitement optimisé pour grandes quantités de données
        """
        import time

        _logger.info("=" * 80)
        _logger.info("DÉBUT DE LA SUPPRESSION DES DOUBLONS")
        _logger.info("=" * 80)

        try:
            # Charger les clients par batch
            batch_size = 500
            offset = 0
            clients_dict = {}
            clients_dict_inverse = {}
            total_traites = 0

            while True:
                # Charger un batch
                clients_batch = self.env['liste.client'].search([], limit=batch_size, offset=offset)

                if not clients_batch:
                    break

                _logger.info(f"Chargement du batch {offset}-{offset + len(clients_batch)}...")

                # Traiter ce batch
                for client in clients_batch:
                    nom = (client.nom or '').strip().upper()
                    prenom = (client.prenom or '').strip().upper()

                    if not nom or not prenom:
                        continue

                    # Dictionnaire normal
                    key_normal = (nom, prenom)
                    if key_normal not in clients_dict:
                        clients_dict[key_normal] = []
                    clients_dict[key_normal].append(client.id)

                    # Dictionnaire inversé
                    key_inverse = (prenom, nom)
                    if key_inverse not in clients_dict_inverse:
                        clients_dict_inverse[key_inverse] = []
                    clients_dict_inverse[key_inverse].append(client.id)

                total_traites += len(clients_batch)
                offset += batch_size

                # Commit et pause
                self.env.cr.commit()
                time.sleep(0.2)

            _logger.info(f"Total de {total_traites} clients analysés")
            _logger.info("Début de la détection des doublons...")

            # Détecter les doublons
            doublons_traites = set()
            records_a_supprimer = []
            nb_groupes = 0

            # Doublons normaux
            for key, client_ids in clients_dict.items():
                if len(client_ids) > 1:
                    clients_non_traites = [cid for cid in client_ids if cid not in doublons_traites]

                    if len(clients_non_traites) > 1:
                        nb_groupes += 1
                        groupe = self.env['liste.client'].browse(clients_non_traites)

                        for cid in clients_non_traites:
                            doublons_traites.add(cid)

                        # Garder celui avec risque élevé
                        record_a_garder = groupe.filtered(lambda r: r.risque == 'eleve')
                        if not record_a_garder:
                            record_a_garder = groupe.sorted(lambda r: r.create_date)[0]
                        else:
                            record_a_garder = record_a_garder[0]

                        records_a_supprimer.extend((groupe - record_a_garder).ids)

            # Doublons inversés
            for key_normal, client_ids in clients_dict.items():
                nom, prenom = key_normal
                key_inverse = (prenom, nom)

                if key_inverse in clients_dict and key_normal != key_inverse:
                    client_ids_inverses = clients_dict[key_inverse]
                    tous_ids = list(set(client_ids + client_ids_inverses))
                    clients_non_traites = [cid for cid in tous_ids if cid not in doublons_traites]

                    if len(clients_non_traites) > 1:
                        nb_groupes += 1
                        groupe = self.env['liste.client'].browse(clients_non_traites)

                        for cid in clients_non_traites:
                            doublons_traites.add(cid)

                        record_a_garder = groupe.filtered(lambda r: r.risque == 'eleve')
                        if not record_a_garder:
                            record_a_garder = groupe.sorted(lambda r: r.create_date)[0]
                        else:
                            record_a_garder = record_a_garder[0]

                        records_a_supprimer.extend((groupe - record_a_garder).ids)

            _logger.info(f"{nb_groupes} groupes de doublons détectés")

            # Supprimer par petits batch
            nb_supprimes = len(records_a_supprimer)
            if records_a_supprimer:
                delete_batch_size = 100
                for i in range(0, len(records_a_supprimer), delete_batch_size):
                    batch = records_a_supprimer[i:i + delete_batch_size]
                    self.env['liste.client'].browse(batch).unlink()
                    _logger.info(f"Supprimé: {min(i + delete_batch_size, nb_supprimes)}/{nb_supprimes}")
                    self.env.cr.commit()
                    time.sleep(0.5)

            _logger.info("=" * 80)
            _logger.info(f"TERMINÉ: {nb_groupes} groupes, {nb_supprimes} suppressions")
            _logger.info("=" * 80)

            # Envoyer notification à l'admin
            admin_user = self.env.ref('base.user_admin')
            if admin_user:
                self.env['mail.message'].create({
                    'subject': 'Suppression des doublons terminée',
                    'body': f'<p>La suppression des doublons est terminée:</p>'
                            f'<ul>'
                            f'<li>{nb_groupes} groupes de doublons trouvés</li>'
                            f'<li>{nb_supprimes} enregistrements supprimés</li>'
                            f'</ul>',
                    'model': 'res.users',
                    'res_id': admin_user.id,
                    'message_type': 'notification',
                })

        except Exception as e:
            _logger.error(f"ERREUR lors de la suppression des doublons: {str(e)}", exc_info=True)
            raise
