from django.dispatch import receiver
from django.shortcuts import render, redirect, HttpResponse
from packages.signals import preCreatePacakge, preSubmitPackage
from databases.signals import preCreateDatabase, preSubmitDBCreation
from ftp.signals import preCreateFTPAccount, preSubmitFTPCreation
import os
import json
import subprocess, shlex



@receiver(preCreatePacakge)
def createPackage(sender, **kwargs):
    from loginSystem.models import Administrator
    from loginSystem.views import loadLoginPage
    from plogical.acl import ACLManager
    try:
        request = kwargs['request']
        userID = request.session['userID']
        currentACL = ACLManager.loadedACL(userID)

        if ACLManager.currentContextPermission(currentACL, 'createPackage') == 0:
            return ACLManager.loadError()


        admin = Administrator.objects.get(pk=userID)
        return render(request, 'beautifulNames/createPackage.html', {"admin": admin.userName})

    except KeyError:
        return redirect(loadLoginPage)

@receiver(preSubmitPackage)
def submitPackage(sender, **kwargs):
        from packages.models import Package
        from loginSystem.models import Administrator
        from plogical.acl import ACLManager
        try:
            request = kwargs['request']
            userID = request.session['userID']

            currentACL = ACLManager.loadedACL(userID)
            if ACLManager.currentContextPermission(currentACL, 'createPackage') == 0:
                return ACLManager.loadErrorJson('saveStatus', 0)

            data = json.loads(request.body)
            packageName = data['packageName']
            packageSpace = int(data['diskSpace'])
            packageBandwidth = int(data['bandwidth'])
            packageDatabases = int(data['dataBases'])
            ftpAccounts = int(data['ftpAccounts'])
            emails = int(data['emails'])
            allowedDomains = int(data['allowedDomains'])

            if packageSpace < 0 or packageBandwidth < 0 or packageDatabases < 0 or ftpAccounts < 0 or emails < 0 or allowedDomains < 0:
                data_ret = {'saveStatus': 0, 'error_message': "All values should be positive or 0."}
                json_data = json.dumps(data_ret)
                return HttpResponse(json_data)

            admin = Administrator.objects.get(pk=userID)

            package = Package(admin=admin, packageName=packageName, diskSpace=packageSpace,
                              bandwidth=packageBandwidth, ftpAccounts=ftpAccounts, dataBases=packageDatabases,
                              emailAccounts=emails, allowedDomains=allowedDomains)

            package.save()

            data_ret = {'saveStatus': 1, 'error_message': "None"}
            json_data = json.dumps(data_ret)
            return HttpResponse(json_data)

        except BaseException, msg:
            data_ret = {'saveStatus': 0, 'error_message': str(msg)}
            json_data = json.dumps(data_ret)
            return HttpResponse(json_data)

@receiver(preCreateDatabase)
def createDatabase(sender, **kwargs):
    from plogical.acl import ACLManager
    try:
        request = kwargs['request']
        userID = request.session['userID']

        currentACL = ACLManager.loadedACL(userID)
        if ACLManager.currentContextPermission(currentACL, 'createDatabase') == 0:
            return ACLManager.loadError()

        websitesName = ACLManager.findAllSites(currentACL, userID)

        return render(request, 'beautifulNames/createDatabase.html', {'websitesList': websitesName})
    except BaseException, msg:
        return HttpResponse(str(msg))

@receiver(preSubmitDBCreation)
def submitDBCreation(sender, **kwargs):
    from plogical.acl import ACLManager
    from plogical.mysqlUtilities import mysqlUtilities
    try:
        request = kwargs['request']
        userID = request.session['userID']

        currentACL = ACLManager.loadedACL(userID)
        if ACLManager.currentContextPermission(currentACL, 'createDatabase') == 0:
            return ACLManager.loadErrorJson('createDBStatus', 0)

        data = json.loads(request.body)
        databaseWebsite = data['databaseWebsite']
        dbName = data['dbName']
        dbUsername = data['dbUsername']
        dbPassword = data['dbPassword']

        dbName = dbName
        dbUsername = dbUsername

        result = mysqlUtilities.submitDBCreation(dbName, dbUsername, dbPassword, databaseWebsite)

        if result[0] == 1:
            data_ret = {'createDBStatus': 1, 'error_message': "None"}
            json_data = json.dumps(data_ret)
            return HttpResponse(json_data)
        else:
            data_ret = {'createDBStatus': 0, 'error_message': result[1]}
            json_data = json.dumps(data_ret)
            return HttpResponse(json_data)
    except BaseException, msg:
        data_ret = {'createDBStatus': 0, 'error_message': str(msg)}
        json_data = json.dumps(data_ret)
        return HttpResponse(json_data)

@receiver(preCreateFTPAccount)
def createFTPAccount(sender, **kwargs):
    from loginSystem.models import Administrator
    from plogical.acl import ACLManager
    try:
        request = kwargs['request']
        userID = request.session['userID']
        currentACL = ACLManager.loadedACL(userID)

        if ACLManager.currentContextPermission(currentACL, 'createFTPAccount') == 0:
            return ACLManager.loadError()

        admin = Administrator.objects.get(pk=userID)

        if not os.path.exists('/home/cyberpanel/pureftpd'):
            return render(request, "ftp/createFTPAccount.html", {"status": 0})

        websitesName = ACLManager.findAllSites(currentACL, userID)

        return render(request, 'beautifulNames/createFTPAccount.html',
                          {'websiteList': websitesName, 'admin': admin.userName, "status": 1})
    except BaseException, msg:
        return HttpResponse(str(msg))

@receiver(preSubmitFTPCreation)
def submitFTPCreation(sender, **kwargs):
    from loginSystem.models import Administrator
    from plogical.acl import ACLManager
    from plogical.virtualHostUtilities import virtualHostUtilities
    from ftp.models import Users
    try:
        request = kwargs['request']
        userID = request.session['userID']
        currentACL = ACLManager.loadedACL(userID)

        if ACLManager.currentContextPermission(currentACL, 'createFTPAccount') == 0:
            return ACLManager.loadErrorJson('creatFTPStatus', 0)

        data = json.loads(request.body)
        userName = data['ftpUserName']
        password = data['ftpPassword']
        path = data['path']
        domainName = data['ftpDomain']

        admin = Administrator.objects.get(id=userID)

        if len(path) > 0:
            pass
        else:
            path = 'None'

        execPath = "sudo python " + virtualHostUtilities.cyberPanel + "/plogical/ftpUtilities.py"

        execPath = execPath + " submitFTPCreation --domainName " + domainName + " --userName " + userName \
                   + " --password " + password + " --path " + path + " --owner " + admin.userName

        output = subprocess.check_output(shlex.split(execPath))

        if output.find("1,None") > -1:
            userTemp = admin.userName + "_" + userName
            user = Users.objects.get(user=userTemp)
            user.user = userName
            user.save()
            data_ret = {'creatFTPStatus': 1, 'error_message': 'None'}
            json_data = json.dumps(data_ret)
            return HttpResponse(json_data)
        else:
            data_ret = {'creatFTPStatus': 0, 'error_message': output}
            json_data = json.dumps(data_ret)
            return HttpResponse(json_data)

    except BaseException, msg:
        data_ret = {'creatFTPStatus': 0, 'error_message': str(msg)}
        json_data = json.dumps(data_ret)
        return HttpResponse(json_data)