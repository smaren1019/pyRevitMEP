# coding: utf8
import rpw
# noinspection PyUnresolvedReferences
from Autodesk.Revit.DB import ParameterType
# noinspection PyUnresolvedReferences
from rpw import revit, DB, UI
# noinspection PyUnresolvedReferences
from System import Guid
import csv


class SharedParameter:
    def __init__(self, name, group, parameter_type, visible=True, guid=None):
        if not guid:
            self.guid = Guid.NewGuid()
        else:
            self.guid = guid
        self.visible = visible
        if isinstance(ParameterType.Text, ParameterType):
            self.type = type
        elif parameter_type in ParameterType.GetNames(DB.ParameterType):
            self.type = getattr(ParameterType, parameter_type)
        else:
            selected_type = rpw.ui.forms.SelectFromList("Select ParameterType",
                                                        ParameterType.GetNames(ParameterType),
                                                        "Invalid ParameterType please select a parameter type")
            self.type = getattr(ParameterType, selected_type)
        self.group = group
        self.name = name

    @staticmethod
    def read_from_csv(csv_path=None):
        if not csv_path:
            csv_path = rpw.ui.forms.select_file(extensions='csv Files (*.csv*)|*.csv*', title='Select File',
                                                multiple=False, restore_directory=True)

        csv_file = open(csv_path)
        file_reader = csv.reader(csv_file)

        shared_parameter_list = []

        for row in file_reader:
            row_len = len(row)
            if row_len < 3:
                print("Line {} is invalid, less than 3 column".format(file_reader.line_num))
            name, group, type = row[0:3]
            visible = True
            guid = None
            if row_len > 4:
                visible = bool(row[3])
            if row_len > 5:
                guid = Guid(row[4])

            shared_parameter_list.append(SharedParameter(name, group, type, visible, guid))
            print(shared_parameter_list)

        return shared_parameter_list

    def write_to_definition_file(self, warning=True):
        """
        Create a new parameter definition in cVrrent shared parameter file
        :param warning: warn user if a definition with given name already exist
        :return: definition
        """
        definition_file = revit.app.OpenSharedParameterFile()
        if not definition_file:
            raise LookupError("No shared parameter file")

        for dg in definition_file.Groups:
            if dg.Name == self.group:
                definition_group = dg
                break
        else:
            definition_group = definition_file.Groups.Create(self.group)

        for definition in definition_group.Definitions:
            if definition.Name == self.name:
                if warning:
                    print("A parameter definition named {} already exist")
                break
        else:
            external_definition_create_options = DB.ExternalDefinitionCreationOptions(self.name,
                                                                                      self.type,
                                                                                      GUID=self.guid,
                                                                                      Visible=self.visible)
            definition = definition_group.Definitions.Create(external_definition_create_options)

        return definition


def create_shared_parameter_definition(revit_app, name, group_name, parameter_type, visible=True):
    # Open shared parameter file
    definition_file = revit_app.OpenSharedParameterFile()
    if not definition_file:
        raise LookupError("No shared parameter file")

    for dg in definition_file.Groups:
        if dg.Name == group_name:
            definition_group = dg
            break
    else:
        definition_group = definition_file.Groups.Create(group_name)

    for definition in definition_group.Definitions:
        if definition.Name == name:
            break
    else:
        external_definition_create_options = DB.ExternalDefinitionCreationOptions(name, parameter_type)
        definition = definition_group.Definitions.Create(external_definition_create_options)

    return definition


def create_project_parameter(revit_app, definition, category_set, built_in_parameter_group, instance):
    if instance:
        binding = revit_app.Create.NewInstanceBinding(category_set)
    else:
        binding = revit.app.Create.NewTypeBinding(category_set)
    parameter_bindings = revit.doc.ParameterBindings
    parameter_bindings.Insert(definition, binding, built_in_parameter_group)