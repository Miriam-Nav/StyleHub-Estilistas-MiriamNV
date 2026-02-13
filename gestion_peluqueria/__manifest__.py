{
    'name': 'Gestión de Peluquería StyleHub',
    'version': '1.0',
    'category': 'Services',
    'summary': 'Gestión de citas, servicios y estilistas',
    'depends': ['base'], 
    'data': [
        'security/ir.model.access.csv',
        'views/peluqueria_servicio_views.xml',
        'views/peluqueria_estilista_views.xml', 
        'views/peluqueria_cita_views.xml',
        'views/peluqueria_res_partner_views.xml',
        'views/peluqueria_actions.xml',
        'views/peluqueria_menu.xml'
    ],
    'installable': True,
    'application': True,
}