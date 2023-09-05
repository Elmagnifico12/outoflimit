/**
 * 简介：ipa 安装器

 * 使用场景：可随时随安装自己备份在手机里的 ipa 包

 * 服务端部署方法：
    1、要有一个可以运行 PHP 环境并且支持 https 访问的服务器
    2、把 api.php 上传到你的服务器中 https://raw.githubusercontent.com/meishixiu/JSBox-ipa-install.js/master/api.php
    3、在 JSBox 中运行本脚本并配置好 api 接口地址和 token (密码)

 * 手机上安装 ipa 方法：
    1、在电脑上把需要的 ipa 备份到手机的 iCloud Drive 或者 Shu 这类文件管理器中
    2、在这些文件管理器中点击分享按钮，打开分享面板，ipa 导入到 JSBox 里，然后“IPA 安装器”进行安装

 * 作者：https://t.me/HaoDou
 
 */

// 避免键盘遮挡住输入框
$app.autoKeyboardEnabled = true

// 默认上传配置
var config = {
  api: 'https://ray.tinggs.com/ipa/api.php',      // 上传接口
  token: 'XKu$6Yff#WvY23dK',    // 上传令牌
};
if ($drive.exists("ipa/upload.conf")) {
  config = JSON.parse($drive.read("ipa/upload.conf").string)
}

var ipa_data = $context.data  // 从 Action Extension 上导入 ipa

if (typeof(ipa_data) == "undefined"){
  // 界面
  $ui.render({
    props: {
      title: "上传配置",
    },
    layout: $layout.fill,
    views: [
      {
        type: "button",
        props: {
          title: "保存配置"
        },
        layout: function (make) {
          make.left.right.bottom.inset(10)
          make.height.equalTo(32)
        },
        events: {
          tapped: function(sender) {
            var cfg = {
              api: $("api").text,
              token: $("token").text,
            };

            // 创建 ipa 文件夹
            var exists = $file.exists("drive://ipa/")
            var isDirectory = $file.isDirectory("drive://ipa/")
            if(!exists && !isDirectory){
              var success = $file.mkdir("drive://ipa/")
            }

            // 保存配置
            var success = $drive.write({
              data: $data({
                string: JSON.stringify(cfg)
              }),
              path: "ipa/upload.conf"
            })

            if(success){
              $ui.alert({
                title: "提示",
                message: "保存成功",
              })
            }else{
              $ui.alert({
                title: "提示",
                message: "保存失败",
              })
            }
          }
        },
      },
      {
        type: "list",
        layout: function (make) {
          make.left.top.right.equalTo(0)
          make.bottom.equalTo($("button").top).offset(0)
        },
        props: {
          rowHeight: 90,
          data: [
            {
              title: "上传接口",
              rows: [{
                type: "text",
                props: {
                  id: 'api',
                  text: config.api || '',
                },
                layout: function (make) {
                  make.edges.inset(5);
                }
              }]
            },
            {
              title: "上传令牌",
              rows: [{
                type: "text",
                props: {
                  id: 'token',
                  text: config.token || '',
                },
                layout: function (make) {
                  make.edges.inset(5);
                }
              }]
            },
          ]
        },
      },
    ],
  })
}else{  // 导入并安装 ipa
  if (ipa_data.fileName.indexOf(".ipa") == -1){
    $ui.alert({
      title: "提示",
      message: "请从分享面板导入 ipa 文件",
      actions: [
        {
          title: "确定",
          handler: function() {
            $context.close()
            $app.close()
          }
        }
      ]
    })
  }else{
    var timestamp = Math.round(new Date().getTime() / 1000)
  
    // 上传 ipa 文件
    $http.upload({
      url: config.api,
      form: {
        token: config.token
      },
      files: [
        {
          "data": ipa_data,
          "name": "file",
          "filename": timestamp
        }
      ],
      showsProgress: false,
      progress: function(percentage) {
        $ui.progress(percentage, "ipa 上传中...")
      },
      handler: function(resp) {
        if(!resp.data.status){
            $ui.alert({
              title: "错误",
              message: resp.data.msg,
              actions: [
                {
                  title: "确定",
                  handler: function() {
                    $context.close()
                    $app.close()
                  }
                }
              ]
            })
        }else{
          $app.openURL("itms-services://?action=download-manifest&url="+resp.data.plist)
        }
      }
    })
  }
}

