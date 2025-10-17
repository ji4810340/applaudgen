from abc import ABC, abstractmethod
from typing import Optional, Union
from jinja2 import Environment
from ..utils import *

class SchemaClassBuilder(ABC):

    template_name: str
    enum_template_name: str

    def __init__(self, jinja_env: Environment, name: str, fields: dict, is_model_class: bool=False, parent: str=None) -> None:
        self.jinja_env = jinja_env
        self.name = name
        self.fields = fields
        self.is_model_class = is_model_class
        self.parent = parent

        self.attributes = []
        self.nested_enums = []
        self.nested_classes = []
        self.remain_enums = {}
    
    @abstractmethod
    def union_type_code(self, item_type: str) -> str:
        pass
    
    @abstractmethod
    def list_type_code(self, item_type: Union[str, list]) -> str:
        pass

    @abstractmethod
    def model_internal_class_name(self) -> str:
        pass

    @abstractmethod
    def external_enum_name(self) -> str:
        pass

    @abstractmethod
    def entitlements_type_code(self) -> str:
        pass

    @abstractmethod
    def canonical_type_code(self, type: str, format: str = None) -> str:
        pass

    @abstractmethod
    def build_attribute_code(self, name: str, type: str, is_required: bool, default_value: str, is_deprecated: bool) -> tuple[str, str]:
        pass

    __trace_enum_map = {
        'Device.Attributes.DeviceClass':    'DeviceClass',
        'Device.Attributes.Status':         'DeviceStatus',
        'AgeRatingDeclaration.Attributes.AlcoholTobaccoOrDrugUseOrReferences': 'AgeRatingDeclarationLevel',
        'AgeRatingDeclaration.Attributes.Contests':                         'AgeRatingDeclarationLevel',
        'AgeRatingDeclaration.Attributes.GamblingSimulated':                'AgeRatingDeclarationLevel',
        'AgeRatingDeclaration.Attributes.MedicalOrTreatmentInformation':    'AgeRatingDeclarationLevel',
        'AgeRatingDeclaration.Attributes.ProfanityOrCrudeHumor':            'AgeRatingDeclarationLevel',
        'AgeRatingDeclaration.Attributes.SexualContentGraphicAndNudity':    'AgeRatingDeclarationLevel',
        'AgeRatingDeclaration.Attributes.SexualContentOrNudity':            'AgeRatingDeclarationLevel',
        'AgeRatingDeclaration.Attributes.HorrorOrFearThemes':               'AgeRatingDeclarationLevel',
        'AgeRatingDeclaration.Attributes.MatureOrSuggestiveThemes':         'AgeRatingDeclarationLevel',
        'AgeRatingDeclaration.Attributes.ViolenceCartoonOrFantasy':         'AgeRatingDeclarationLevel',
        'AgeRatingDeclaration.Attributes.ViolenceRealisticProlongedGraphicOrSadistic': 'AgeRatingDeclarationLevel',
        'AgeRatingDeclaration.Attributes.ViolenceRealistic':    'AgeRatingDeclarationLevel',
        'AppClipAdvancedExperience.Attributes.Status':          'AppClipAdvancedExperienceStatus',
        'AppClipAdvancedExperience.Attributes.PlaceStatus':     'AppClipAdvancedExperiencePlaceStatus',
        'AppClipAdvancedExperience.Attributes.BusinessCategory': 'AppClipAdvancedExperienceBusinessCategory',
        'AppClipDomainStatus.Attributes.Domain.ErrorCode':      'AppClipDomainErrorCode',
        'AppStoreVersion.Attributes.ReleaseType':               'AppStoreVersionReleaseType',
        'App.Attributes.ContentRightsDeclaration':              'AppContentRightsDeclaration',
        'BuildBundle.Attributes.BundleType':                    'BuildBundleType',
        'Build.Attributes.ProcessingState':                     'BuildProcessingState',
        'CiArtifact.Attributes.FileType':                       'CiArtifactFileType',
        'CiBuildRun.Attributes.StartReason':                    'CiBuildRunStartReason',
        'CiBuildRun.Attributes.CancelReason':                   'CiBuildRunCancelReason',
        'CiIssue.Attributes.IssueType':                         'CiIssueType',
        'CiProduct.Attributes.ProductType':                     'CiProductType',
        'InAppPurchase.Attributes.InAppPurchaseType':           'InAppPurchaseType',
        'InAppPurchase.Attributes.State':                       'InAppPurchaseState',
        'PerfPowerMetric.Attributes.MetricType':                'PerfPowerMetricType',
        'Profile.Attributes.ProfileType':                       'ProfileType',
        'Profile.Attributes.ProfileState':                      'ProfileState',
        'AppClipAdvancedExperience.Attributes.Place.DisplayPoint.Source': 'AppClipAdvancedExperiencePlaceSource',
        'AppClipAdvancedExperience.Attributes.Place.MapAction':     'AppClipAdvancedExperiencePlaceMapAction',
        'AppClipAdvancedExperience.Attributes.Place.Relationship':  'AppClipAdvancedExperiencePlaceRelationship',
        'AppClipAdvancedExperience.Attributes.Place.PhoneNumber.Type': 'AppClipAdvancedExperiencePlacePhoneNumberType',
        'PerfPowerMetric.Attributes.Platform':                  'PerfPowerMetricPlatform',
        'DiagnosticSignature.Attributes.DiagnosticType':        'DiagnosticType',
    }

    def build_enum_code(self, name: str, values: list) -> str:
        return self.jinja_env.get_template(f'{self.enum_template_name}.jinja').render(
            name=name,
            values=values
        )

    def __parse_property_type(self, property_name: str, property_dict: dict) -> tuple[str, str, bool]:
        deprecated = property_dict.get('deprecated', False)

        if '$ref' in property_dict:
            return (property_dict['$ref'].split('/')[-1], None, deprecated)
        else:
            default_value = None
            property_type = property_dict.get('type', None)
            parent_name = f'{self.parent}.{self.name}' if self.parent else self.name

            if property_type == 'string' and 'enum' in property_dict:
                enum = property_dict['enum']
                if len(enum) == 1 and property_name == 'type':
                    # type is a single enum value
                    default_value = f'"{enum[0]}"'
                else:
                    possible_model_internal_class_name = self.model_internal_class_name(property_name)
                    possile_external_enum_name = self.external_enum_name(enum)

                    if not self.is_model_class and (possible_model_internal_class_name or possile_external_enum_name):
                        property_type = possible_model_internal_class_name or possile_external_enum_name
                    else:
                        property_type = capfirst(property_name)
                        trace = f'{parent_name}.{property_type}'
                        if trace in self.__trace_enum_map:
                            # print(f'<~~~ {trace} ~~~>')
                            property_type = self.__trace_enum_map[trace]
                            self.remain_enums[property_type] = enum
                        else:
                            # print(f'<--- {trace} --->')
                            enum_code = self.build_enum_code(property_type, enum)
                            self.nested_enums.append(enum_code)

                    if len(enum) == 1:
                        # enum is a single value
                        default_value = f'{property_type}.{safe_enum_name(enum[0])}'
            elif property_type == 'object':
                if property_name == "place" and not self.is_model_class:
                    property_type = "AppClipAdvancedExperience.Attributes.Place"
                elif property_name == "entitlements":
                    property_type = self.entitlements_type_code()
                elif 'properties' in property_dict:
                    sub_class_builder = self.__class__(self.jinja_env, capfirst(property_name), property_dict, self.is_model_class, parent_name)
                    sub_class_code = sub_class_builder.build()
                    if sub_class_code is not None:  # Only add if not None
                        self.nested_classes.append(sub_class_code)
                    self.remain_enums.update(sub_class_builder.remain_enums)
                    property_type = capfirst(property_name)
                elif 'additionalProperties' in property_dict:
                    # Object with additionalProperties but no defined properties - use dict
                    property_type = 'dict'
                else:
                    assert False, f'Cannot handle type ({property_type}) in class {self.name}'
            elif property_type == 'array':
                items = property_dict['items']
                item_type = items.get('type', None)

                if item_type == 'object':
                    item_type_name = capfirst(simple_singular(property_name))
                    item_class_builder = self.__class__(self.jinja_env, item_type_name, items, self.is_model_class, parent_name)
                    item_class_code = item_class_builder.build()
                    if item_class_code is not None:
                        self.nested_classes.append(item_class_code)
                    self.remain_enums.update(item_class_builder.remain_enums)
                    property_type = self.list_type_code(item_type_name)
                elif item_type == 'string':
                    property_type = self.list_type_code(f"string")
                elif item_type == 'array':
                    # Array of arrays - create a nested class for the inner array
                    item_type_name = capfirst(simple_singular(property_name))
                    item_class_builder = self.__class__(self.jinja_env, item_type_name, items, self.is_model_class, parent_name)
                    item_class_code = item_class_builder.build()
                    if item_class_code is not None:
                        self.nested_classes.append(item_class_code)
                    self.remain_enums.update(item_class_builder.remain_enums)
                    property_type = self.list_type_code(item_type_name)
                elif '$ref' in items:
                    '''
                    "items" : {
                        "$ref" : "#/components/schemas/AppClipDefaultExperienceLocalization"
                    }
                    '''
                    property_type = self.list_type_code(f"{items['$ref'].split('/')[-1]}")
                elif 'oneOf' in items:
                    '''
                    "items" : {
                        "oneOf" : [ {
                            "$ref" : "#/components/schemas/AppClipDefaultExperience"
                        },
                        …
                    }
                    '''
                    # included field, discriminator is `type` attribute of contained object
                    union_types = [ref['$ref'].split('/')[-1] for ref in items['oneOf'] if '$ref' in ref]
                    property_type = self.list_type_code(union_types)
                else:
                    assert False, f'Not supported array type ({items}) in class {self.name}'
            elif 'oneOf' in property_dict:
                # ErrroResponse.source, no discriminator
                union_types = []
                for idx, ref in enumerate(property_dict['oneOf']):
                    if '$ref' in ref:
                        union_types.append(ref['$ref'].split('/')[-1])
                    elif ref.get('type') == 'string':
                        # Inline string type - just use str
                        union_types.append('str')
                    elif ref.get('type') == 'object':
                        # Inline object type - create a nested class
                        nested_class_name = capfirst(property_name) + f'Option{idx + 1}'
                        nested_class_builder = self.__class__(self.jinja_env, nested_class_name, ref, self.is_model_class, parent_name)
                        nested_class_code = nested_class_builder.build()
                        if nested_class_code is not None:
                            self.nested_classes.append(nested_class_code)
                        self.remain_enums.update(nested_class_builder.remain_enums)
                        union_types.append(nested_class_name)
                # Remove duplicates while preserving order
                seen = set()
                union_types = [x for x in union_types if not (x in seen or seen.add(x))]
                property_type = self.union_type_code(union_types) if union_types else 'str'
            else:
                type_format = property_dict.get('format', None)
                property_type = self.canonical_type_code(property_type, type_format)
                # assert False, f'Cannot handle type ({property_type}) in class {self.name}'

            return (property_type, default_value, deprecated)

    def build(self, super_class: Optional[str] = None) -> str:
        if 'enum' in self.fields.keys():
            assert self.fields['type']=='string', "Unkown type in enum!"
            return self.build_enum_code(self.name, self.fields['enum'])

        # If it's just an array type (has type and items but no properties), treat it as a simple type alias
        if self.fields.get('type') == 'array' and 'items' in self.fields and 'properties' not in self.fields:
            # This is a type alias for an array, not a class
            # We'll just skip it and let the parent handle it
            return None
        
        # If it's an object with only additionalProperties (like a map/dict), skip it
        if self.fields.get('type') == 'object' and 'additionalProperties' in self.fields and 'properties' not in self.fields:
            # This is a dict/map type, not a class
            return None

        allowed_field_keys = ['type', 'title', 'required', 'properties', 'deprecated']

        # Check keys to make sure we have handled all types in classes
        assert all(field_key in allowed_field_keys for field_key in self.fields.keys()), f'Contains unknown field key ({self.fields.keys()}) in class {self.name}'
        
        deprecated = self.fields.get('deprecated', False)
        properties = self.fields['properties']
        required_property_names = self.fields['required'] if 'required' in self.fields else []

        sorted_property_names = required_property_names + [name for name in properties.keys() if name not in required_property_names]

        for property_name in sorted_property_names:
            property_dict = properties[property_name]
            is_required = property_name in required_property_names

            property_type, default_value, is_deprecated = self.__parse_property_type(property_name, property_dict)

            self.attributes.append(self.build_attribute_code(property_name, property_type, is_required, default_value, is_deprecated))

        return self.jinja_env.get_template(f'{self.template_name}.jinja').render(
            name=self.name,
            super_class = super_class if super_class else 'ApplaudModel',
            deprecated=deprecated,
            nested_classes=self.nested_classes,
            nested_enums=self.nested_enums,
            attributes=self.attributes
        )
