from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime

class PeluqueriaCita(models.Model):
    _name = 'peluqueria.cita'
    _description = 'Cita de Peluquería'
    _order = "fecha_inicio desc"

    # Nombre de la cita
    _rec_name = 'display_name_cita'
    display_name_cita = fields.Char(string='Nombre de la Cita', compute='_compute_display_name_cita', store=True)

    # Un cliente puede tener muchas citas
    # res.partner: modulo do odoo donde se encuentren los Clientes
    cliente_id = fields.Many2one('res.partner', string='Cliente', required=True, 
        domain=[
        ('is_company', '=', False),
        ('name', 'not ilike', 'Administrator'),
        ('name', 'not ilike', 'Simplified Invoice')
    ])

    es_cliente_vip = fields.Boolean(compute='_compute_es_cliente_vip')

    # Un estilista puede tener muchas citas
    estilista_id = fields.Many2one('peluqueria.estilista', string='Estilista', required=True)
    
    fecha_inicio = fields.Datetime(string='Fecha y Hora de Inicio', required=True)

    fecha_fin = fields.Datetime( string='Fecha y Hora de Fin', compute='_compute_fecha_fin', store=True)

    estado_cita = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmada', 'Confirmada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
    ], string='Estado', default='borrador')

    color_agenda = fields.Integer(compute='_compute_color_agenda')

    # Una cita puede tener varias líneas.
    servicio_linea_ids = fields.One2many( 'peluqueria.cita.linea', 'cita_id', string='Servicios Solicitados', required=True)

    # Precio total calculado con la funcion _compute_precio_total
    precio_total = fields.Float( string='Total', compute='_compute_precio_total')

    # Comrpueba que el cliente es VIP
    @api.depends('cliente_id.category_id')
    def _compute_es_cliente_vip(self):
        for record in self:
            # Revisa si entre las etiquetas del cliente existe una llamada 'VIP'
            tags = record.cliente_id.category_id.mapped('name')
            record.es_cliente_vip = any(tag.upper() == 'VIP' for tag in tags)

    # Nombre de la cita
    @api.depends('cliente_id', 'estilista_id', 'es_cliente_vip')
    def _compute_display_name_cita(self):
        for record in self:
            nombre_cliente = record.cliente_id.name or "Sin Cliente"
            nombre_estilista = record.estilista_id.name or "Sin Estilista"
            
            estrella = "⭐ " if record.es_cliente_vip else ""
            
            record.display_name_cita = f"{estrella}{nombre_cliente} - {nombre_estilista}"

    # Calcula el precio total sumando el precio_unitario del servicio de cada linea
    @api.depends('servicio_linea_ids.precio_unitario')
    def _compute_precio_total(self):
        for cita in self:
            cita.precio_total = sum(
                linea.precio_unitario
                for linea in cita.servicio_linea_ids
            )

    # Calcula la duración total para establecer la fecha_fin
    @api.depends('fecha_inicio', 'servicio_linea_ids.duracion_servicio')
    def _compute_fecha_fin(self):
        for cita in self:
            if cita.fecha_inicio:
                # Suma las duraciones de todas las líneas
                duracion_total = sum(linea.duracion_servicio for linea in cita.servicio_linea_ids)
                # Guarda el Datetime y timedelta permite transformar a horas y sumar
                cita.fecha_fin = cita.fecha_inicio + timedelta(hours=duracion_total)
            else:
                cita.fecha_fin = False

    # Al guardar o modificar la fecha de inicio, la de fin o el estilista, se ejecuta esta función.
    @api.constrains('fecha_inicio', 'fecha_fin', 'estilista_id')
    def _check_disponibilidad_estilista(self):
        for record in self:
            # Busca otras citas del mismo estilista que se solapen
            solapamiento = self.search([
                # Ignora la cita que se está editando
                ('id', '!=', record.id), 
                ('estilista_id', '=', record.estilista_id.id),
                ('estado_cita', '!=', 'cancelada'),
                ('fecha_inicio', '<', record.fecha_fin),
                ('fecha_fin', '>', record.fecha_inicio),
            ])
            if solapamiento:
                raise ValidationError(
                    f"El estilista {record.estilista_id.name} "
                    "ya tiene una cita programada en ese horario."
                )

    # Cambiar color de cita en calendario
    def _compute_color_agenda(self):
        for record in self:
            if record.estado_cita == 'borrador':
                record.color_agenda = 0
            elif record.estado_cita == 'confirmada':
                record.color_agenda = 4
            elif record.estado_cita == 'realizada':
                record.color_agenda = 10
            elif record.estado_cita == 'cancelada':
                record.color_agenda = 1
            else:
                record.color_agenda = 0

    # Validar valores positivos (Precio)
    @api.constrains('precio_total')
    def _check_precio_positivo(self):
        for record in self:
            if record.precio_total < 0:
                raise ValidationError("El precio no puede ser negativo.")

    # Validar fechas pasadas
    @api.constrains('fecha_inicio')
    def _check_fecha_futura(self):
        for record in self:
            if record.fecha_inicio and record.fecha_inicio < datetime.now():
                raise ValidationError("No puedes programar una cita en una fecha pasada.")
    
    # Actualizar VIP
    def _actualizar_etiqueta_vip(self, cliente):
        if not cliente:
            return

        # Cuenta las citas realizadas de este cliente
        citas_count = self.env['peluqueria.cita'].search_count([
            ('cliente_id', '=', cliente.id),
            ('estado_cita', '=', 'realizada')
        ])

        # Busca la etiqueta VIP
        tag = self.env['res.partner.category'].search([('name', '=', 'VIP')], limit=1)
        
        # Si llega a 5
        if citas_count >= 5:
            # Si no está la crea
            if not tag:
                tag = self.env['res.partner.category'].create({'name': 'VIP', 'color': 3})
            
            # Solo la añade si no la tiene ya
            if tag not in cliente.category_id:
                cliente.write({'category_id': [(4, tag.id)]})
        else:
            # Si tiene menos de 5 y tiene la etiqueta, se la quita
            if tag and tag in cliente.category_id:
                # El comando (3, ID) quita la relación entre el cliente y la etiqueta
                cliente.write({'category_id': [(3, tag.id)]})
                   
    # Métodos para los botones del Header
    def action_confirmar(self):   
        self.write({'estado_cita': 'confirmada'})    

    def action_finalizar(self):
        # Cambia el estado de la cita
        self.write({'estado_cita': 'realizada'})

    def action_cancelar(self):
        for record in self:
            # No se puede cancelar si está en borrador
            if record.estado_cita == 'borrador':
                raise ValidationError("No puedes cancelar una cita que aún está en borrador.")
        self.write({'estado_cita': 'cancelada'})
    
    # Captura cualquier cambio (botones o edición manual)
    def write(self, vals):
        # Guarda los cambios en la base de datos
        res = super(PeluqueriaCita, self).write(vals)
        
        # Si se cambia el estado o el cliente recalcula
        if 'estado_cita' in vals or 'cliente_id' in vals:
            for record in self:
                record._actualizar_etiqueta_vip(record.cliente_id)
        return res
