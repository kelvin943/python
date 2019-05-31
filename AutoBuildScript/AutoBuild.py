
#coding=utf-8

import os
from optparse import OptionParser
from biplist import *
import subprocess
import requests

ScriptPath            = 'AutoBuildScript/'
ExportOptionsPlist    = ScriptPath + 'ExportOptionsAutomic.plist'
ConfigurationFileName = ScriptPath + 'Configuration.plist'


class AutoBuildTools():
    def __init__(self, options):
        self.project       = options.project
        self.workspace     = options.workspace
        self.scheme        = options.scheme
        self.output        = options.output
        self.config        = options.configuration
        self.deployment    = options.deployment
        self.archiveMethod = options.archiveMethod
        # 参数检查
        if self.project is None and self.workspace is None:
            print (' must select -p (project) or -w (workspore) to archive .Please try again')
            return

        if self.scheme is None:
            print ('-s (scheme) cannot be nil on workspace ,it requires a parameter.Please try again')
            return

        if self.config.find('Debug') != -1 or self.config.find('debug') != -1:
            self.config = 'Debug'

        #导出包的目录默认是ScriptPath/target 下
        # if self.output is None or len(self.output) < 1:
        #     dir = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop');
        #     self.output = dir + '/%s-%s'%(self.scheme,self.config)

        if self.deployment is not None:
            self.deployment = self.deployment.lower()
            if self.deployment.find('fir') != -1:
                self.deployment = 'fir'
            elif self.deployment.find('pgy') != -1:
                self.deployment = 'pgy'
            else:#不上传分发网站
                self.deployment = ''

        if self.archiveMethod is not None:
            self.archiveMethod = self.archiveMethod.lower()
            if self.archiveMethod.find('store') != -1 or self.archiveMethod.find('appstore') != -1 or self.archiveMethod.find('app-store')!=-1:
                self.archiveMethod = "app-store"
            elif self.archiveMethod.find('hoc') !=-1 or self.archiveMethod.find('adhoc') != -1 or self.archiveMethod.find('ad-hoc')!=-1:
                self.archiveMethod = 'ad-hoc'
            elif self.archiveMethod.find('enterprise') !=-1:
                self.archiveMethod = 'enterprise'
            else:
                self.archiveMethod = 'development'


    def localConfigurationsFromFile(self):
        #config file
        plist = readPlist(ConfigurationFileName)
        #entitle file
        exportOptionPlistData = readPlist(ExportOptionsPlist)
        #pgy
        pgyData = plist.get('pgy')
        if pgyData is not None:
            self.pgyUserKey    = pgyData['PgyUserKey']
            self.pgyApiKey     = pgyData['PgyApiKey']
            self.pgyBaseUrl    = pgyData['PgyBaseUrl']
            self.pgyUploadUrl  = pgyData['PgyUploadUrl']
            # del entitlePlistData['pgy']

        #fir
        firData = plist.get('fir')
        if firData is not None:
            self.firUploadUrl    = firData['FirBaseUrl']
            self.firToken        = firData['FirToken']
            # del entitlePlistData['fir']

        #手动签名还是自动签名Automatic/Manual
        self.signingStyel =plist.get('signingStyle')
        self.confitPlist = plist

        #写入打包的方法
        exportOptionPlistData['method'] = self.archiveMethod
        if self.archiveMethod == 'enterprise':
           exportOptionPlistData['teamID'] = plist['teamID-enterprise']
        else:
           exportOptionPlistData['teamID'] = plist['teamID-company']
        writePlist(exportOptionPlistData, ExportOptionsPlist)
        try:
            print('write ExportOptionsPlist.plist success !!!!')
        except (InvalidPlistException, NotBinaryPlistException) as err:
            print("error : write ExportOptionsPlist file fail"), err

    def buildProject(self):
        print ('-----开始构建project-------------------')

    def buildWorkSpace(self):
        if self.signingStyel == 'Automatic':
            print ('-----signingStyel:%s-------------------' % (self.signingStyel))
            print ('-----开始打包workspace-------------------')
            process = subprocess.Popen("pwd", stdout = subprocess.PIPE)
            (stdoutdata, stderrdata) = process.communicate()
            archiveDir = stdoutdata.decode().strip() +'/'+ ScriptPath + 'Archive/%s.xcarchive' % (self.scheme)
            print ('archiveDir: ' + archiveDir)
            archiveCmd = 'xcodebuild archive  \
                            -workspace %s  \
                            -scheme %s\
                            -configuration %s  \
                            -archivePath %s  \
                            -sdk iphoneos  \
                            -quiet clean  \
                            -allowProvisioningUpdates \
                             archive' %  \
            (self.workspace, self.scheme, self.config, archiveDir)
            print ('-----excute cmd:' + archiveCmd)
            process = subprocess.Popen(archiveCmd, shell=True)
            process.wait()
            archiveReturnCode = process.returncode
            if archiveReturnCode != 0:
                print('archive failed')
                return None
            else :
                print('archive success')
                return archiveDir

        elif self.signingStyel == 'Manual':
            if self.archiveMethod == 'app-store':
                configData =  self.confitPlist.get('App-StoreConfig')
            elif self.archiveMethod == 'ad-hoc':
                configData =  self.confitPlist.get('Ad-HocConfig')
            elif self.archiveMethod == 'development':
                configData =  self.confitPlist.get('EnterpriseConfig')
            elif self.archiveMethod == 'enterprise':
                configData =  self.confitPlist.get('EnterpriseConfig')
            # 读取手动管理的配置信息
            BundleID             = configData['BundleID']
            CODE_SIGN_IDENTITY   = configData['CODE_SIGN_IDENTITY']
            PROVISIONING_PROFILE = configData['PROVISIONING_PROFILE']
            print ('-----ArchiveMethod:%s\n-----BundleID:%s\n-----CODE_SIGN_IDENTITY:%s\n-----PROVISIONING_PROFILE:%s'%(self.archiveMethod,BundleID,CODE_SIGN_IDENTITY,PROVISIONING_PROFILE))

            print ('-----signingStyel:%s-------------------' % (self.signingStyel))
            print ('-----开始打包workspace-------------------')
            process = subprocess.Popen("pwd", stdout = subprocess.PIPE)
            (stdoutdata, stderrdata) = process.communicate()
            archiveDir = stdoutdata.decode().strip() +'/'+ ScriptPath + 'Archive/%s.xcarchive' % (self.scheme)

            print ('archiveDir: ' + archiveDir)
            archiveCmd = 'xcrun  xcodebuild -workspace %s -scheme %s -configuration %s -archivePath %s  -quiet clean archive build CODE_SIGN_IDENTITY ="%s" PROVISIONING_PROFILE="%s" PRODUCT_BUNDLE_IDENTIFIER="%s" ' % (
            self.workspace, self.scheme, self.config, archiveDir,CODE_SIGN_IDENTITY,PROVISIONING_PROFILE,BundleID)
            print ('-----excute cmd:' + archiveCmd)
            process = subprocess.Popen(archiveCmd, shell=True)
            process.wait()

            print ('-----开始导出IPA-------------------')
            # exportArchiveCmd = 'xcrun xcodebuild -exportArchive -archivePath %s -exportPath %s -exportOptionsPlist %s' % (
            # archiveDir, self.output, EntitlementsName, self.config)
            # process = subprocess.Popen(exportArchiveCmd, shell=True)
            # (stdoutdata, stderrdata) = process.communicate()

            # ipaPath = self.output + ('/%s.ipa' % (self.scheme))

    def uploadIpaToPgyer(self,ipaPath):
        print ('ipaPath: %s' % (ipaPath)) 
        # ipaPath = os.path.expanduser(ipaPath)
        # ipaPath = unicode(ipaPath, "utf-8")
        files = {'file': open(ipaPath, 'rb')}
        headers = {'enctype':'multipart/form-data'}
        payload = {'uKey':self.pgyUserKey,'_api_key':self.pgyApiKey,'publishRange':'2','isPublishToPublic':'2', 'password':'123456', 'updateDescription':''}
        print ('uploading....')
        r = requests.post(self.pgyUploadUrl, data = payload ,files=files,headers=headers)
        if r.status_code == requests.codes.ok:
            result = r.json()
            resultCode = result['code']
            if resultCode == 0:
                downUrl = self.pgyBaseUrl + result['data']['appShortcutUrl']
                print ('Upload Success')
                print ('DownUrl is:' + downUrl)
            else:
                print ('Upload Fail!')
                print ('Reason:' + result['message'])
        else:
            print ('HTTPError,Code:'+r.status_code)

    def uploadIpaToFir(ipaPath):
        print('do not support fir yet')



    # start build
    def startBuild(self):
        # load local configuration settings
        self.localConfigurationsFromFile()

        #默认构建workspce
        if self.workspace is not None:
            archivePath = self.buildWorkSpace()
            # archivePath = os.getcwd() + '/'+ ScriptPath + ('Archive/%s.xcarchive' % (self.scheme))
            if archivePath is not None:
                self.exportAndUpload(archivePath)
        elif self.project is not None:
            archivePath = self.buildProject()
            if archivePath is not None:
                self.exportAndUpload(archivePath)

    def exportAndUpload(self,archivePath):
        print ('-----开始导出IPA-------------------------')
        exportArchiveCmd = 'xcrun xcodebuild  \
                            -exportArchive  \
                            -archivePath %s  \
                            -exportPath %s  \
                            -exportOptionsPlist %s' % \
        (archivePath, self.output, ExportOptionsPlist)
        process = subprocess.Popen(exportArchiveCmd, shell=True)
        (stdoutdata, stderrdata) = process.communicate()

        signReturnCode = process.returncode
        if signReturnCode != 0:
            print('export ipa failed')
        else:
            ipaPath = self.output + ('%s.ipa' % (self.scheme))
            if self.deployment == 'pgy':
                self.uploadIpaToPgyer(ipaPath)
            elif self.deployment == 'fir':
                self.uploadIpaToFir(ipaPath)
            else:
                print('export ipa successed')




def main():
     # 解析参数内容
    parser = OptionParser()
    parser.add_option("-w", "--workspace", help="Build the workspace name.xcworkspace.", metavar="name.xcworkspace")
    parser.add_option("-p", "--project",help="Build the project name.xcodeproj",metavar ="name.xcodepro")
    parser.add_option("-s", "--scheme",help="Build the scheme specified by schemename. Required if building a workspace.",
                      metavar="schemename")
    parser.add_option("-m", "--archiveMethod", help="specify archive mode,app-store/enterprise/ad-hoc/development",default='enterprise')
    parser.add_option("-c", "--configuration", help="specify ipa Debug/Release", metavar="config",default='Release')
    parser.add_option("-o", "--output", help="specify output filePath+filename", metavar="output_filePath+filename",default= ScriptPath +'target/')

    parser.add_option("-d", "--deployment", help="deployment web target pgy/fir or upload appstore", metavar="distribute")

    customArgs = ['-w','/Users/zhangquan526/project/SmartOperation.iOS/SmartOperationMobile.xcworkspace','-s','OPS','--archiveMethod','development','-d','pgy']
    (options, args) = parser.parse_args(customArgs)
    print('options: %s ,args: %s' % (options,args))
    buildTools = AutoBuildTools(options)
    buildTools.startBuild()

if __name__ == '__main__':
    main()

