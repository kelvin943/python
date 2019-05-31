
#coding=utf-8

import os
from optparse import OptionParser
from biplist import *

import subprocess

EntitlementsName = 'Entitlements.plist'
ConfigurationFileName = 'Configuration.plist'


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

        if self.config is None or len(self.config) < 1:
            self.config = 'Debug'

        if self.output is None or len(self.output) < 1:
            dir = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop');
            self.output = dir + '/%s-%s'%(self.scheme,self.config)
        if self.archiveMethod is not None:
            self.archiveMethod = self.archiveMethod.lower()
            if self.archiveMethod.find('store') != -1 or self.archiveMethod.find('appstore') != -1 or self.archiveMethod.find('app-store')!=-1:
                self.archiveMethod = "app-store"
            elif self.archiveMethod.find('hoc') !=-1 or self.archiveMethod.find('adhoc') != -1 or self.archiveMethod.find('ad-hoc')!=-1:
                self.archiveMethod = 'ad-hoc'
            elif self.archiveMethod.find('development') !=-1:
                self.archiveMethod = 'development'
            #默认是企业包
            else:
                self.archiveMethod = 'enterprise'

    # load config settings
    def localConfigurationsFromFile(self):
        #config file
        plist = readPlist(ConfigurationFileName)
        #entitle file
        entitlePlistData = plist
        #pgy
        pgyData = plist.get('pgy')
        if pgyData is not None:
            self.pgyUserKey    = pgyData['PgyUserKey']
            self.pgyApiKey     = pgyData['PgyApiKey']
            self.pgyBaseUrl    = pgyData['PgyBaseUrl']
            self.pgyUploadUrl  = pgyData['PgyUploadUrl']
            del entitlePlistData['pgy']

        #fir
        firData = plist.get('fir')
        if firData is not None:
            self.firUploadUrl    = firData['FirBaseUrl']
            self.firToken        = firData['FirToken']
            del entitlePlistData['fir']
        #写入打包的方法
        entitlePlistData['method'] = self.archiveMethod

        writePlist(entitlePlistData, EntitlementsName)
        try:
            print('write Entitlements.plist success !!!!')
        except (InvalidPlistException, NotBinaryPlistException) as err:
            print("error : write entitlements file fail"), err

    def buildWorkSpace(self):
        print ('--------------开始打包workspace-------------------')
        process = subprocess.Popen("pwd", stdout = subprocess.PIPE)
        (stdoutdata, stderrdata) = process.communicate()
        archiveDir = stdoutdata.decode().strip() + '/Archive/%s.xcarchive' % (self.scheme)
        print ('archiveDir: ' + archiveDir)
        archiveCmd = 'xcodebuild archive -workspace %s -scheme %s -configuration %s -archivePath %s -sdk iphoneos' % (
        self.workspace, self.scheme, self.config, archiveDir)
        process = subprocess.Popen(archiveCmd, shell=True)
        process.wait()

        print ('--------------开始导出IPA-------------------')
        exportArchiveCmd = 'xcrun xcodebuild -exportArchive -archivePath %s -exportPath %s -exportOptionsPlist %s' % (
        archiveDir, self.output, EntitlementsName, self.config)
        process = subprocess.Popen(exportArchiveCmd, shell=True)
        (stdoutdata, stderrdata) = process.communicate()

        ipaPath = self.output + ('/%s.ipa' % (self.scheme))


    def buildProject(self):
        print ('--------------开始构建project-------------------')

    # start build
    def startBuild(self):
        # load local configuration settings
        self.localConfigurationsFromFile()

        #默认构建workspce
        if self.workspace is not None:
            self.buildWorkSpace()
        elif self.project is not None:
            self.buildProject()




def main():
     # 解析参数内容
    parser = OptionParser()
    parser.add_option("-w", "--workspace", help="Build the workspace name.xcworkspace.", metavar="name.xcworkspace")
    parser.add_option("-p", "--project",help="Build the project name.xcodeproj",metavar ="name.xcodepro")
    parser.add_option("-s", "--scheme",help="Build the scheme specified by schemename. Required if building a workspace.",
                      metavar="schemename")
    parser.add_option("-o", "--output", help="specify output filePath+filename", metavar="output_filePath+filename")
    parser.add_option("-c", "--configuration", help="specify ipa Debug/Release", metavar="config",default='Release')
    parser.add_option("-m", "--archiveMethod", help="specify archive mode,app-store/enterprise/ad-hoc/development",default='enterprise')
    parser.add_option("-d", "--deployment", help="deployment web target pgy/fir", metavar="distribute")
    
    customArgs = ['-w','/Users/zhangquan526/project/SmartOperation.iOS/SmartOperationMobile.xcworkspace','-s','OPS','-m','appstore','arg1', 'arg2']
    (options, args) = parser.parse_args(customArgs)
    print('options: %s ,args: %s' % (options,args))   
    buildTools = AutoBuildTools(options)
    buildTools.startBuild()

if __name__ == '__main__':
    main()


    
