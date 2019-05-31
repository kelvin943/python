# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from optparse import OptionParser
import subprocess
import requests
import os
import json
from biplist import *

import smtplib
from email.mime.text import MIMEText
from email.header import Header

import qrcode
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

import time

EntitlementsName = 'Entitlements.plist'
ConfigurationFileName = 'Configuration.plist'


class WaterMarkerImage():
    def __init__(self, imgMode='RGBA', bg_color=(255, 255, 255)):
        self.imgMode = imgMode
        self.bg_color = bg_color


    def waterMarker(self, title,desc,fg_color=(0,0,0),
                 fontsize=13):
        '''Generate the Image of letters'''

        self.title = title
        self.desc = desc
        self.fg_color = fg_color
        self.fontsize = fontsize
        self.font = ImageFont.truetype('/Library/Fonts/PingFang.ttc', self.fontsize)

        (self.letterWidth, self.letterHeight) = self.font.getsize(desc)

        self.drawBrush = ImageDraw.Draw(self.backgroudImage)

        self.drawBrush.text((10, 15), self.title, fill=self.fg_color, font=self.font)
        bg_w,bg_h = self.backgroudImage.size
        self.drawBrush.text((10,bg_h - 25),self.desc,fill=self.fg_color, font=self.font)

    def qrcodeimage(self,qrsource, iconsourcePath):
        self.qrsource = qrsource
        self.iconsourcePath = iconsourcePath

        # 初步生成二维码图像
        qr = qrcode.QRCode(version=5, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=6, border=4)
        qr.add_data(qrsource)
        qr.make(fit=True)

        img = qr.make_image()
        img = img.convert(self.imgMode)

        # 打开logo文件
        icon = Image.open(iconsourcePath)

        # 计算logo的尺寸
        img_w, img_h = img.size
        factor = 4
        size_w = int(img_w / factor)
        size_h = int(img_h / factor)

        # 重新设置logo文件的尺寸
        icon_w, icon_h = icon.size
        if icon_w > size_w:
            icon_w = size_w

        if icon_h > size_h:
            icon_h = size_h

        icon = icon.resize((icon_w, icon_h), Image.ANTIALIAS)

        # 计算logo的位置，并贴到二维码图像中
        w = int((img_w - icon_w) / 2)
        h = int((img_h - icon_h) / 2)
        icon = icon.convert('RGBA')

        img.paste(icon, (w, h), icon)

        # self.backgroudImage.resize((img_w + 60, img_h+100), Image.ANTIALIAS)
        self.backgroudImage = Image.new(self.imgMode,(img_w + 20, img_h+40), self.bg_color);

        (self.bgImg_w,self.bgImg_h) = self.backgroudImage.size
        self.backgroudImage.paste(img,(int((self.bgImg_w-img_w)/2),25),img)

    def saveImg(self, saveName=''):
        # if '' == saveName.strip():
        # 	saveName = str(self.desc.encode('gb2312')) + '.png'
        # fileName, file_format = saveName.split('.')
        # fileName += '_' + str(self.fontsize) + '.' + file_format

        fileName = time.strftime("%Y-%m-%d %H.%M.%S", time.localtime())
        fileName = 'QRImage' + fileName + '.png'
        fileName = os.path.join(os.path.join(os.path.expanduser("~"), 'Desktop'), fileName)
        self.backgroudImage.save(fileName, format='png')

    def Show(self):
        self.backgroudImage.show()


class AutoBuild():
    def __init__(self,options):

        self.project = options.project
        self.workspace = options.workspace
        self.scheme = options.scheme
        self.output = options.output
        self.config = options.configuration
        self.deployment = options.deployment

        self.archiveMethod = options.archiveMethod

        if self.archiveMethod is not None:
            self.archiveMethod = self.archiveMethod.lower()
            if self.archiveMethod.find('store') != -1 or self.archiveMethod.find('appstore') != -1:
                self.archiveMethod = 'app-store'
            elif self.archiveMethod.find('hoc') != -1 or self.archiveMethod.find('adhoc') != -1:
                self.archiveMethod = 'ad-hoc'

        if self.scheme is None and self.workspace is None:
            if self.project is not None:
                pComp = self.project.split('.')
                self.scheme = pComp[0]

        if self.scheme is None:
            print ('-s (scheme) cannot be nil,it requires a parameter.Please try again')
            return

        if self.project is None and self.workspace is None:
            print ('-p parameter cannot be nil.Please try again')
            return
        if self.config is None or len(self.config) < 1:
            self.config = 'Debug'

        if self.output is None or len(self.output) < 1:
            dir = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop');
            self.output = dir + '/%s-%s'%(self.scheme,self.config)


    # load config settings
    def localConfigurationsFromFile(self):

        plist = readPlist(ConfigurationFileName)

        #entitle file
        entitlePlistData = plist

        if self.archiveMethod is None:
            self.archiveMethod = plist.get('archiveMethod', 'enterprise')

        entitlePlistData['method'] = self.archiveMethod

        #pgy
        pgyData = plist.get('pgy')
        if pgyData is not None:
            self.pgyUserKey = pgyData['PgyUserKey']
            self.pgyApiKey = pgyData['PgyApiKey']
            self.pgyBaseUrl = pgyData['PgyBaseUrl']
            self.pgyUploadUrl = pgyData['PgyUploadUrl']
            del entitlePlistData['pgy']

        #fir
        firData = plist.get('fir')
        if firData is not None:
            self.firUploadUrl = firData['FirBaseUrl']
            self.firToken = firData['FirToken']
            del entitlePlistData['fir']

        writePlist(entitlePlistData, EntitlementsName)
        try:
            print ('write Entitlements.plist success !!!!')
        except (InvalidPlistException, NotBinaryPlistException) as err:
            print ("error : write entitlements file fail"), err


    def increaseBuildVersion(self,versionStr):

        num = int(versionStr)
        incMethod = lambda x: x + 1
        num = incMethod(num)

        resultStr = str(num)
        while len(resultStr) < 3:
            resultStr = '0' + resultStr

        global buildVersionNumb
        buildVersionNumb = resultStr

        return resultStr

    def findInfoPlistFile(self, fileName, root='.'):
        dirs = []
        matchs = []

        for currentName in os.listdir(root):
            if currentName == 'Products':
                continue

            addRootName = os.path.join(root, currentName)
            if os.path.isdir(addRootName):
                dirs.append(addRootName)
            elif os.path.isfile(addRootName) and fileName in addRootName:
                matchs.append(addRootName)

                if addRootName is not None:
                    plist = readPlist(addRootName)
                    versionStr = plist['CFBundleVersion']
                    nVersionNum = self.increaseBuildVersion(versionStr)
                    plist['CFBundleVersion'] = nVersionNum
                    self.bundleVersion = plist['CFBundleShortVersionString']

                    writePlist(plist, addRootName)

                break

        if len(matchs) < 1:
            for dir in dirs:
                self.findInfoPlistFile(fileName, dir)


    def cleanBuildDir(self,buildDir):
        cleanCmd = "rm -r %s" % (buildDir)
        process = subprocess.Popen(cleanCmd, shell=True)
        process.wait()
        print "cleaned buildDir: %s" % (buildDir)

    def findAppIconFile(self,fileName, root='.'):
        dirs = []
        matchs = []
        self.iconImagePath = ''

        for currentName in os.listdir(root):
            if currentName == 'Products' or currentName == 'Archive' or currentName == 'distribute':
                continue
            elif currentName.startswith('.') or currentName.endswith('.framework') or currentName.endswith(
                    '.xcodeproj'):
                continue

            addRootName = os.path.join(root, currentName)
            if os.path.isdir(addRootName):
                if fileName in addRootName:
                    matchs.append(addRootName)
                    # print addRootName
                    contents = os.listdir(addRootName)
                    for img in contents:
                        if img.endswith('.png') or img.endswith('.jpg'):
                            self.iconImagePath = os.path.join(addRootName, img)
                            break;

                else:
                    dirs.append(addRootName)

        if len(self.iconImagePath) > 0:
            return self.iconImagePath

        if len(matchs) < 1:
            for dir in dirs:
                self.findAppIconFile(fileName, dir)
                if len(self.iconImagePath) > 0:
                    break

    def showDownloadUrl(self,downUrl):
        self.findAppIconFile('AppIcon.appiconset')

        configurationSetting = u'测试环境'

        if self.config.lower().find('release') != -1:
            configurationSetting = u'正式环境'

        waterMarkerImage = WaterMarkerImage()
        waterMarkerImage.qrcodeimage(downUrl, self.iconImagePath)

        desc = u'iOS实惠app V'+self.bundleVersion+'(build' + buildVersionNumb+') '+configurationSetting
        waterMarkerImage.waterMarker(u'下载地址:' + downUrl, desc)

        waterMarkerImage.saveImg()
        waterMarkerImage.Show()

    def parserUploadResult(self,jsonResult):
        resultCode = jsonResult['code']
        if resultCode == 0:
            downUrl = self.pgyBaseUrl + jsonResult['data']['appShortcutUrl']
            print "Upload Success"
        if downUrl is not None:
            self.showDownloadUrl(downUrl)
        else:
            print "Upload Fail!"
            print "Reason:" + jsonResult['message']

    def uploadIpaToPgyer(self,ipaPath):
        print "ipaPath:" + ipaPath
        files = {'file': open(ipaPath, 'rb')}
        headers = {'enctype': 'multipart/form-data'}

        payload = {'uKey': self.pgyUserKey, '_api_key': self.pgyApiKey, 'publishRange': '2', 'isPublishToPublic': '2'}

        print "uploading...."
        r = requests.post(self.pgyUploadUrl, data=payload, files=files, headers=headers)
        if r.status_code == requests.codes.ok:
            result = r.json()
            self.parserUploadResult(result)
        else:
            print 'HTTPError,Code:' + r.status_code

    def uploadToFir(self,ipaPath):
        httpAddress = None
        if os.path.exists(ipaPath):
            ret = os.popen("fir p '%s' -T '%s'" % (ipaPath, self.firToken))
            sep = 'Published succeed:'
            for info in ret.readlines():
                if info and sep in info:
                    split = info.find(sep)
                    httpAddress = info[split + len(sep) + 1:]
                    break
        else:
            print "------warning :no ipa file"
        return httpAddress

    def sendEmailDownloadUrl(self,url):

        to = raw_input('请输入收件邮箱：')

        user = "faneyoung@126.com"
        pwd = "faneyoung163"

        msg = MIMEText('有新包了~下载地址:%s' % url, 'plain', 'utf-8')
        msg["From"] = user
        msg["To"] = to

        subject = '请下载最新的包进行体验'
        msg['Subject'] = Header(subject, 'utf-8')

        try:
            # SSL + 465 / noSSL+587
            s = smtplib.SMTP_SSL("smtp.126.com", 587)
            s.EnableSsl = False
            s.Timeout = 15000000
            s.login(user, pwd)
            s.sendmail(user, to, msg.as_string())
            s.quit()
            print "Success!"
        except smtplib.SMTPException, e:
            print "Falied,%s" % e

    def handleIpa(self,ipaPath, deploymeet):

        if deploymeet is None:
            self.uploadIpaToPgyer(ipaPath)
        else:
            if deploymeet.find('fir') != -1 or deploymeet.find('Fir') != -1 or deploymeet.find('FIR') != -1:
                urlAddr = self.uploadToFir(ipaPath)
                if urlAddr is not None:
                    inputStr = raw_input('是否发送通知邮件 y/n :')
                    if inputStr is not None:
                        if isinstance(inputStr, basestring):
                            if inputStr == 'y' or inputStr == 'Y':
                                self.sendEmailDownloadUrl(urlAddr)

                        self.showDownloadUrl(downUrl=urlAddr)

            else:
                self.uploadIpaToPgyer(ipaPath)

    def buildProject(self):
        process = subprocess.Popen("pwd", stdout=subprocess.PIPE)
        (stdoutdata, stderrdata) = process.communicate()

        archiveDir = stdoutdata.strip() + '/Archive/%s.xcarchive' % (self.scheme)
        print "archiveDir: " + archiveDir

        archiveCmd = 'xcodebuild archive -project %s -scheme %s -configuration %s -archivePath %s' % (
        self.project, self.scheme, self.config, archiveDir)
        process = subprocess.Popen(archiveCmd, shell=True)
        process.wait()

        exportArchiveCmd = 'xcodebuild -exportArchive -archivePath %s -exportPath %s -exportOptionsPlist %s -configuration %s ' % (
        archiveDir, self.output, EntitlementsName, self.config)

        process = subprocess.Popen(exportArchiveCmd, shell=True)
        (stdoutdata, stderrdata) = process.communicate()
        print '--------------archive finished,uploading -> -> -> ---------------'

        ipaPath = self.output + ('/%s.ipa' % (self.scheme))
        self.handleIpa(ipaPath, self.deployment)

        # cleanBuildDir("./build")
        self.cleanBuildDir(archiveDir)

    def buildWorkspace(self):
        process = subprocess.Popen("pwd", stdout=subprocess.PIPE)
        (stdoutdata, stderrdata) = process.communicate()

        archiveDir = stdoutdata.strip() + '/Archive/%s.xcarchive' % (self.scheme)
        print "archiveDir: " + archiveDir
        archiveCmd = 'xcodebuild archive -workspace %s -scheme %s -configuration %s -archivePath %s build' % (
        self.workspace, self.scheme, self.config, archiveDir)
        process = subprocess.Popen(archiveCmd, shell=True)
        process.wait()

        exportArchiveCmd = 'xcodebuild -exportArchive -archivePath %s -exportPath %s -exportOptionsPlist %s -configuration %s ' % (
        archiveDir, self.output, EntitlementsName, self.config)
        process = subprocess.Popen(exportArchiveCmd, shell=True)
        (stdoutdata, stderrdata) = process.communicate()

        ipaPath = self.output + ('/%s.ipa' % (self.scheme))
        self.handleIpa(ipaPath, self.deployment)

        self.cleanBuildDir(archiveDir)

    def startBuild(self):
        # load local configuration settings
        self.localConfigurationsFromFile()

        #plist file
        self.findInfoPlistFile(self.scheme + '-Info.plist')

        if self.project is not None:
            self.buildProject()
        elif self.workspace is not None:
            self.buildWorkspace()


def main():
    parser = OptionParser()
    parser.add_option("-w", "--workspace", help="Build the workspace name.xcworkspace.", metavar="name.xcworkspace")
    parser.add_option("-p", "--project", help="Build the project name.xcodeproj.", metavar="name.xcodeproj")
    parser.add_option("-s", "--scheme",
                      help="Build the scheme specified by schemename. Required if building a workspace.",
                      metavar="schemename")
    parser.add_option("-o", "--output", help="specify output filePath+filename", metavar="output_filePath+filename")
    parser.add_option("-c", "--configuration", help="specify ipa debug/release", metavar="config")
    parser.add_option("-m", "--archiveMethod", help="specify archive mode,app-store/enterprise/ad-hoc/development",
                      metavar="method")
    parser.add_option("-d", "--deployment", help="deployment web target pgy/fir", metavar="distribute")

    (options, args) = parser.parse_args()

    print "options: %s, args: %s" % (options, args)

    autobuild = AutoBuild(options)
    autobuild.startBuild()


if __name__ == '__main__':
    main()

    