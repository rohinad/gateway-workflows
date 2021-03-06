# Copyright 2017 BlueCat Networks (USA) Inc. and its affiliates
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# By: Bill Morton (bmorton@bluecatnetworks.com)
# Date: 06-12-2017
# Gateway Version: 17.10.1

# Copyright 2017 BlueCat Networks. All rights reserved.

# Various Flask framework items.
import os
import sys

from flask import url_for, redirect, render_template, flash, g

from bluecat import route, util, entity
import config.default_config as config
from main_app import app
from .update_user_permissions_form import GenericFormTemplate
from .util_custom import get_udf_portal_groups

#This will skip the user being updated
access_type_not_update = 'GUI_AND_API'

def module_path():
    encoding = sys.getfilesystemencoding()
    return os.path.dirname(os.path.abspath(unicode(__file__, encoding)))

# The workflow name must be the first part of any endpoints defined in this file.
# If you break this rule, you will trip up on other people's endpoint names and
# chaos will ensue.
@route(app, '/update_user_permissions/update_user_permissions_endpoint')
@util.workflow_permission_required('update_user_permissions_page')
@util.exception_catcher
def update_user_permissions_update_user_permissions_page():
    form = GenericFormTemplate()

    form.gateway_groups.choices = get_udf_portal_groups()

    return render_template(
        'update_user_permissions_page.html',
        form=form,
        text=util.get_text(module_path(), config.language),
        options=g.user.get_options(),
    )

@route(app, '/update_user_permissions/form', methods=['POST'])
@util.workflow_permission_required('update_user_permissions_page')
@util.exception_catcher
def update_user_permissions_update_user_permissions_page_form():
    form = GenericFormTemplate()

    if form.validate_on_submit():
        try:

            #Getting the Group ID from Group selected in the form group in Address Manager
            grpId = g.user.get_api().get_entity_by_id(form.groups.data)

            #Get all users in the group from the groupId
            usrInGrp = entity.Entity.get_linked_entities(grpId, 'User')

            #Update the users UDF.
            #only updates users that are not GUI_AND_API based in the group that is selected in the form gateway_groups
            #Does not update the admin user
            #updates the Access Type to GUI and API. Other Options are (GUI, API)

            #List of all users updated
            updated_users_list = []

            for usr in usrInGrp:
                if not usr.get_property('userAccessType') == access_type_not_update and not usr.get_name() == 'admin':
                    #Updating the user access type to GUI_AND_API
                    usr.set_property('userAccessType', 'GUI_AND_API')

                    #updating the UDF called PortalGroup value to the form data in gateway_groups
                    usr.set_property('PortalGroup', form.gateway_groups.data)

                    #commiting the update
                    usr.update()

                    #Adding the updated user to the list
                    updated_users_list.append(usr.get_name())

            #Changing the list into a string for logging message
            updated_users = ', '.join(updated_users_list)

            #Logging sent to the session log file
            g.user.logger.info('Updated users permissions for ' + str(len(updated_users_list)) + ' users')
            g.user.logger.info('Updated users permissions for users:  ' + updated_users)

            #Message on the form
            flash(' Success - Updated users permissions for ' + str(len(updated_users_list)) + ' users', 'succeed')
            return redirect(url_for('update_user_permissionsupdate_user_permissions_update_user_permissions_page'))

        except Exception as e:
            flash(util.safe_str(e))
            # Log error and render workflow page
            g.user.logger.warning('%s' % util.safe_str(e), msg_type=g.user.logger.EXCEPTION)
            return render_template('update_user_permissions_page.html',
                                   form=form,
                                   text=util.get_text(module_path(), config.language),
                                   options=g.user.get_options())

    else:
        g.user.logger.info('Form data was not valid.')
        return render_template(
            'update_user_permissions_page.html',
            form=form,
            text=util.get_text(module_path(), config.language),
            options=g.user.get_options(),
        )
