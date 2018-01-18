import datetime

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

import ckanext.satreasury.helpers as helpers


PROVINCES = [
    'Eastern Cape',
    'Free State',
    'Gauteng',
    'KwaZulu-Natal',
    'Limpopo',
    'Mpumalanga',
    'North West',
    'Northern Cape',
    'Western Cape',
]

SPHERES = ['national', 'provincial']


class SATreasuryDatasetPlugin(plugins.SingletonPlugin, tk.DefaultDatasetForm):
    """ Plugin for the SA National Treasury CKAN website.
    """
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer
    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')
        tk.add_public_directory(config_, 'public')
        tk.add_resource('fanstatic', 'satreasury')

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        del facets_dict['tags']
        facets_dict['vocab_financial_years'] = 'Financial Year'
        facets_dict['vocab_spheres'] = 'Sphere of Government'
        facets_dict['vocab_provinces'] = 'Province'
        # move to the end
        facets_dict['organization'] = facets_dict.pop('organization')
        facets_dict['license_id'] = facets_dict.pop('license_id')
        facets_dict['groups'] = facets_dict.pop('groups')
        facets_dict['res_format'] = facets_dict.pop('res_format')
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        del facets_dict['tags']
        facets_dict['vocab_financial_years'] = 'Financial Year'
        facets_dict['vocab_provinces'] = 'Province'
        # move to the end
        facets_dict['res_format'] = facets_dict.pop('res_format')
        facets_dict['organization'] = facets_dict.pop('organization')
        facets_dict['groups'] = facets_dict.pop('groups')
        facets_dict['license_id'] = facets_dict.pop('license_id')
        return facets_dict

    # IDatasetForm
    def show_package_schema(self):
        schema = super(SATreasuryDatasetPlugin, self).show_package_schema()
        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))
        schema.update({
            'financial_year': [
                tk.get_converter('convert_from_tags')('financial_years'),
                tk.get_validator('ignore_missing')
            ],
            'province': [
                tk.get_converter('convert_from_tags')('provinces'),
                tk.get_validator('ignore_missing')
            ],
            'sphere': [
                tk.get_converter('convert_from_tags')('spheres'),
                tk.get_validator('ignore_missing')
            ],
            'methodology': [
                tk.get_converter('convert_from_extras'),
                tk.get_validator('ignore_missing')
            ],
        })
        return schema

    def create_package_schema(self):
        schema = super(SATreasuryDatasetPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(SATreasuryDatasetPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def _modify_package_schema(self, schema):
        schema.update({
            'financial_year': [
                tk.get_validator('ignore_missing'),
                tk.get_converter('convert_to_tags')('financial_years')
            ],
            'province': [
                tk.get_validator('ignore_missing'),
                tk.get_converter('convert_to_tags')('provinces')
            ],
            'sphere': [
                tk.get_validator('ignore_missing'),
                tk.get_converter('convert_to_tags')('spheres')
            ],
            'methodology': [
                tk.get_validator('ignore_missing'),
                tk.get_converter('convert_to_extras')
            ],
        })
        return schema

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'financial_years': load_financial_years,
            'provinces': load_provinces,
            'spheres': load_spheres,
            'active_financial_years': helpers.active_financial_years,
            'latest_financial_year': helpers.latest_financial_year,
            'packages_for_latest_financial_year': helpers.packages_for_latest_financial_year,
        }


def create_financial_years():
    """ Ensure all necessary financial years tags exist.
    """
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        vocab = tk.get_action('vocabulary_show')(context, {'id': 'financial_years'})
    except tk.ObjectNotFound:
        vocab = tk.get_action('vocabulary_create')(context, {'name': 'financial_years'})

    tag_create = tk.get_action('tag_create')
    existing = set(t['name'] for t in vocab['tags'])
    for year in set(required_financial_years()) - existing:
        tag_create(context, {
            'name': year,
            'vocabulary_id': vocab['id'],
        })


def load_financial_years():
    create_financial_years()
    try:
        tag_list = tk.get_action('tag_list')
        return tag_list(data_dict={'vocabulary_id': 'financial_years'})
    except tk.ObjectNotFound:
        return None


def required_financial_years():
    # eg. 2017-18
    return ['%s-%s' % (y, y + 1 - 2000)
            for y in xrange(2007, datetime.date.today().year + 2)
            ]


def create_provinces():
    """ Ensure all necessary province tags exist.
    """
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        vocab = tk.get_action('vocabulary_show')(context, {'id': 'provinces'})
    except tk.ObjectNotFound:
        vocab = tk.get_action('vocabulary_create')(context, {'name': 'provinces'})

    tag_create = tk.get_action('tag_create')
    existing = set(t['name'] for t in vocab['tags'])
    for province in set(PROVINCES) - existing:
        tag_create(context, {
            'name': province,
            'vocabulary_id': vocab['id'],
        })


def load_provinces():
    create_provinces()
    try:
        tag_list = tk.get_action('tag_list')
        return tag_list(data_dict={'vocabulary_id': 'provinces'})
    except tk.ObjectNotFound:
        return None


def create_spheres():
    """ Ensure all necessary spheres tags exist.
    """
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        vocab = tk.get_action('vocabulary_show')(context, {'id': 'spheres'})
    except tk.ObjectNotFound:
        vocab = tk.get_action('vocabulary_create')(context, {'name': 'spheres'})

    tag_create = tk.get_action('tag_create')
    existing = set(t['name'] for t in vocab['tags'])
    for sphere in set(SPHERES) - existing:
        tag_create(context, {
            'name': sphere,
            'vocabulary_id': vocab['id'],
        })


def load_spheres():
    create_spheres()
    try:
        tag_list = tk.get_action('tag_list')
        return tag_list(data_dict={'vocabulary_id': 'spheres'})
    except tk.ObjectNotFound:
        return None


class SATreasuryOrganizationPlugin(plugins.SingletonPlugin, tk.DefaultOrganizationForm):
    """ Plugin for the SA National Treasury CKAN website.
    """

    plugins.implements(plugins.IGroupForm, inherit=True)

    # IGroupForm

    def group_types(self):
        return ('organization',)

    def group_controller(self):
        return 'organization'

    def form_to_db_schema(self):
         # Import core converters and validators
        _convert_to_extras = plugins.toolkit.get_converter('convert_to_extras')
        _ignore_missing = plugins.toolkit.get_validator('ignore_missing')

        schema = super(SATreasuryOrganizationPlugin, self).form_to_db_schema()
        schema = self._modify_group_schema(schema)

        default_validators = [_ignore_missing, _convert_to_extras]
        schema.update({
            'url': default_validators
        })
        return schema

    def db_to_form_schema(self):
        # Import core converters and validators
        _ignore_missing = plugins.toolkit.get_validator('ignore_missing')

        schema = super(SATreasuryOrganizationPlugin, self).form_to_db_schema()

        default_validators = [custom_convert_from_extras, _ignore_missing]
        schema.update({
            'url': default_validators,
            'telephone': default_validators,
            'facebook_id': default_validators,
            'twitter_id': default_validators,
        })
        return schema

def custom_convert_from_extras(key, data, errors, context):
    for data_key in data.keys():
        if (data_key[0] == 'extras'):
            data_value = data[data_key]
            if(data_value['key'] == key[-1]):
                data[key] = data_value['value']
                del data[data_key]
                break
