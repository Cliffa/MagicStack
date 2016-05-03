# -*- coding:utf-8 -*-

from django.db.models import Q
from assetManage.asset_api import *
from MagicStack.api import *
from MagicStack.models import Setting
from assetManage.forms import AssetForm, IdcForm,NetWorkingForm,NetWorkingGlobalForm,PowerManageForm
from assetManage.models import *
from permManage.perm_api import get_group_asset_perm, get_group_user_perm
from userManage.user_api import user_operator_record
from common.interface import APIRequest
from common.models import Task
import uuid
import time


@require_role('admin')
@user_operator_record
def group_add(request, res,*args):
    """
    Group add view
    添加资产组
    """
    header_title, path1, path2 = '添加资产组', '资产管理', '添加资产组'
    res['operator'] = path2
    asset_all = Asset.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name', '')
        asset_select = request.POST.getlist('asset_select', [])
        comment = request.POST.get('comment', '')

        try:
            if not name:
                emg = '组名不能为空'
                raise ServerError(emg)

            asset_group_test = get_object(AssetGroup, name=name)
            if asset_group_test:
                emg = "该组名 %s 已存在" % name
                raise ServerError(emg)

        except ServerError:
            res['flag'] = 'false'
            res['content'] = emg

        else:
            db_add_group(name=name, comment=comment, asset_select=asset_select)
            smg = "主机组 %s 添加成功" % name
            res['content'] = smg

    return my_render('assetManage/group_add.html', locals(), request)


@require_role('admin')
@user_operator_record
def group_edit(request,res, *args):
    """
    Group edit view
    编辑资产组
    """
    header_title, path1, path2 = '编辑主机组', '资产管理', '编辑主机组'
    res['operator'] = path2
    group_id = request.GET.get('id', '')
    group = get_object(AssetGroup, id=group_id)

    asset_all = Asset.objects.all()
    asset_select = Asset.objects.filter(group=group)
    asset_no_select = [a for a in asset_all if a not in asset_select]

    if request.method == 'POST':
        name = request.POST.get('name', '')
        asset_select = request.POST.getlist('asset_select', [])
        comment = request.POST.get('comment', '')

        try:
            if not name:
                emg = u'组名不能为空'
                raise ServerError(emg)

            if group.name != name:
                asset_group_test = get_object(AssetGroup, name=name)
                if asset_group_test:
                    emg = u"该组名 %s 已存在" % name
                    raise ServerError(emg)

        except ServerError:
            res['flag'] = 'false'
            res['content'] = emg

        else:
            group.asset_set.clear()
            db_update_group(id=group_id, name=name, comment=comment, asset_select=asset_select)
            smg = u"主机组 %s 添加成功" % name
            res['content'] = smg

        return HttpResponseRedirect(reverse('asset_group_list'))

    return my_render('assetManage/group_edit.html', locals(), request)


@require_role('admin')
def group_list(request):
    """
    list asset group
    列出资产组
    """
    header_title, path1, path2 = u'查看资产组', u'资产管理', u'查看资产组'
    keyword = request.GET.get('keyword', '')
    asset_group_list = AssetGroup.objects.all()
    group_id = request.GET.get('id')
    if group_id:
        asset_group_list = asset_group_list.filter(id=group_id)
    if keyword:
        asset_group_list = asset_group_list.filter(Q(name__contains=keyword) | Q(comment__contains=keyword))

    asset_group_list, p, asset_groups, page_range, current_page, show_first, show_end = pages(asset_group_list, request)
    return my_render('assetManage/group_list.html', locals(), request)


@require_role('admin')
@user_operator_record
def group_del(request,res, *args):
    """
    Group delete view
    删除主机组
    """
    res['operator'] = '删除主机组'
    res['content'] = '删除主机组'
    group_ids = request.GET.get('id', '')
    group_id_list = group_ids.split(',')
    for group_id in group_id_list:
        asset_group = AssetGroup.objects.get(id=group_id)
        res['content'] += '%s   ' % asset_group.name
        asset_group.delete()

    return HttpResponse(u'删除成功')


@require_role('admin')
@user_operator_record
def asset_add(request,res, *args):
    """
    Asset add view
    添加资产
    """
    error = msg = ''
    header_title, path1, path2 = '添加资产', '资产管理', '添加资产'
    res['operator'] = path2
    asset_groups = AssetGroup.objects.all()
    asset_nets = NetWorking.objects.all()
    af = AssetForm()
    nfg = NetWorkingGlobalForm()
    nf = NetWorkingForm()
    pf = PowerManageForm()
    if request.method == 'POST':
        try:
            asset_info = Asset()
            asset_info.ip = request.POST.get('ip', '')
            asset_info.name = request.POST.get('name', '')
            asset_info.owerns = request.POST.get('owerns', '')
            asset_info.profile = request.POST.get('profile', '')
            asset_info.status = request.POST.get('status', '1')
            asset_info.kickstart = request.POST.get('kickstart', '')
            asset_info.port = request.POST.get('port',22)
            asset_info.username = request.POST.get('username', 'rooot')
            asset_info.password = request.POST.get('password', '')
            asset_info.idc_id = int(request.POST.get('idc', '1'))
            asset_info.cabinet = request.POST.get('cabinet', '')
            asset_info.number = request.POST.get('number', '')
            asset_info.machine_status = int(request.POST.get('machine_status', 1))
            asset_info.asset_type = int(request.POST.get('asset_type', 1))
            asset_info.sn = request.POST.get('sn', '')
            asset_info.comment = request.POST.get('comment', '')
            asset_info.proxy_id = int(request.POST.get('proxy', '1'))


            nt_g = NetWorkingGlobal()
            nt_g.hostname = request.POST.get('hostname', '')
            nt_g.gateway = request.POST.get('gateway','')
            nt_g.name_servers = request.POST.get('name_servers', '')
            nt_g.save()
            asset_info.networking_g_id = nt_g.id

            pm = PowerManage()
            pm.power_type = request.POST.get('power_type')
            pm.power_address = request.POST.get('power_address')
            pm.power_username = request.POST.get('power_username')
            pm.power_password = request.POST.get('power_password')
            pm.power_id = request.POST.get('power_id',1)
            pm.save()
            asset_info.power_manage_id = pm.id

            asset_info.proxy_id = int(request.POST.get('proxy', 1))
            hostname = request.POST.get('name', '')
            is_active = True if request.POST.get('is_active', '1') == '1' else False
            is_enabled = True if request.POST.get('is_enabled', '1') == '1' else False
            asset_info.netboot_enabled = is_enabled
            asset_info.is_active = is_active
            if Asset.objects.filter(name=unicode(hostname)):
                    error = '该主机名 %s 已存在!' % hostname
                    raise ServerError(error)
            asset_info.save()

            net = NetWorking()
            net.name = request.POST.get('add_name', '')
            net.mac_address = request.POST.get('mac_address', '')
            net.ip_address = request.POST.get('ip_address','')
            net.cnames = request.POST.get('cnames', '')
            net.dns_name = request.POST.get('dns_name', '')
            net.mtu = request.POST.get('mtu', '')
            net.per_gateway = request.POST.get('per_gateway', '')
            net.static = request.POST.get('static', '')
            net.static_routes = request.POST.get('static_routes', '')
            net.subnet_mask = request.POST.get('subnet_mask', '')
            net.save()
            asset_info.networking.add(net)

            group = AssetGroup()
            group_id = request.POST.getlist('group')
            for item in group_id:
                group = AssetGroup.objects.get(id=int(item))
                asset_info.group.add(group)

        except ServerError:
            res['flag'] = 'false'
            res['content'] = error
        else:
            msg = 'add %s success' % hostname
            res['content'] = msg
            fileds = {
                "name": request.POST.get('name'),
                "hostname": request.POST.get('hostname'),
                "profile": request.POST.get('profile'),
                "gateway": request.POST.get('gateway'),
                "power_type": request.POST.get('power_type'),
                "power_address": request.POST.get('power_address'),
                "power_user": request.POST.get('power_username'),
                "power_pass": request.POST.get('power_password'),
                "interfaces": {
                    "eth0":{
                        "mac_address": request.POST.get('mac_address'),
                        "ip_address": request.POST.get('ip_address'),
                        "if_gateway": request.POST.get('per_gateway'),
                        "mtu": request.POST.get('mtu'),
                        "static": 1,
                    },
                }
            }

            data = json.dumps(fileds)
            select_proxy = get_object(Proxy, id=int(request.POST.get('proxy')))
            pro_username = select_proxy.username
            pro_password = select_proxy.password
            pro_url = select_proxy.url
            try:
                api = APIRequest('http://172.16.30.69:8100/v1.0/system/', 'test', '123456')
                result, codes = api.req_post(data)
                # tk = Task()
                # tk.task_name = res['task_name']
                # tk.username = request.user.username
                # tk.status = res['status']
                # tk.url = res['link']
                # tk.start_time = datetime.datetime.now()
            except Exception,e:
                error = e
            else:
                if codes == 200:
                    msg = result['messege']
                else:
                    error = result['messegs']

    return my_render('assetManage/asset_add.html', locals(), request)


@require_role('admin')
def asset_add_batch(request):
    header_title, path1, path2 = u'添加资产', u'资产管理', u'批量添加'
    return my_render('assetManage/asset_add_batch.html', locals(), request)


@require_role('admin')
@user_operator_record
def asset_del(request,res, *args):
    """
    del a asset
    删除主机
    """
    res['operator'] = res['content'] = '删除主机'
    asset_id = request.GET.get('id', '')
    if asset_id:
        Asset.objects.filter(id=asset_id).delete()

    if request.method == 'POST':
        asset_batch = request.GET.get('arg', '')
        asset_id_all = str(request.POST.get('asset_id_all', ''))

        if asset_batch:
            for asset_id in asset_id_all.split(','):
                asset = get_object(Asset, id=asset_id)
                res['content'] += '%s   ' % asset.name
                asset.delete()

    return HttpResponse(u'删除成功')


@require_role(role='super')
@user_operator_record
def asset_edit(request,res, *args):
    """
    edit a asset
    修改主机
    """
    error = msg = ''
    header_title, path1, path2 = u'修改资产', u'资产管理', u'修改资产'
    res['operator'] = path2
    asset_id = request.GET.get('id', '')
    username = request.user.username
    asset_info = get_object(Asset, id=asset_id)
    if asset_info:
        password_old = asset_info.password
    af = AssetForm(instance=asset_info)
    nf = NetWorkingForm(instance=asset_info.networking.all()[0])
    nfg = NetWorkingGlobalForm(instance=asset_info.networking_g)
    pf = PowerManageForm(instance=asset_info.power_manage)
    if request.method == 'POST':
        ip = request.POST.get('ip', '')
        try:
            asset_info.ip = request.POST.get('ip', '')
            asset_info.name = request.POST.get('name', '')
            asset_info.owerns = request.POST.get('owerns', '')
            asset_info.profile = request.POST.get('profile', '')
            asset_info.status = request.POST.get('status', '1')
            asset_info.kickstart = request.POST.get('kickstart', '')
            asset_info.port = request.POST.get('port',22)
            asset_info.username = request.POST.get('username', 'root')
            asset_info.password = request.POST.get('password', '')
            asset_info.idc_id = int(request.POST.get('idc', '1'))
            asset_info.cabinet = request.POST.get('cabinet', '')
            asset_info.number = request.POST.get('number', '')
            asset_info.machine_status = int(request.POST.get('machine_status', 1))
            asset_info.asset_type = int(request.POST.get('asset_type', 1))
            asset_info.sn = request.POST.get('sn', '')
            asset_info.comment = request.POST.get('comment', '')
            asset_info.proxy_id = int(request.POST.get('proxy', '1'))

            #save NetWorkingGlobal
            nt_g = NetWorkingGlobal()
            nt_g.hostname = request.POST.get('hostname', '')
            nt_g.gateway = request.POST.get('gateway','')
            nt_g.name_servers = request.POST.get('name_servers', '')
            nt_g.save()
            asset_info.networking_g_id = nt_g.id

            #save PowerManage
            pm = PowerManage()
            pm.power_type = request.POST.get('power_type')
            pm.power_address = request.POST.get('power_address')
            pm.power_username = request.POST.get('power_username')
            pm.power_password = request.POST.get('power_password')
            pm.power_id = request.POST.get('power_id',1)
            pm.save()
            asset_info.power_manage = pm

            asset_info.proxy_id = int(request.POST.get('proxy', 1))
            hostname = request.POST.get('name', '')
            is_active = True if request.POST.get('is_active', '1') == '1' else False
            is_enabled = True if request.POST.get('is_enabled', '1') == '1' else False
            asset_info.netboot_enabled = is_enabled
            asset_info.is_active = is_active


            net = NetWorking()
            net.name = request.POST.get('net_name', '')
            net.mac_address = request.POST.get('mac_address', '')
            net.ip_address = request.POST.get('ip_address','')
            net.cnames = request.POST.get('cnames', '')
            net.dns_name = request.POST.get('dns_name', '')
            net.mtu = request.POST.get('mtu', '')
            net.per_gateway = request.POST.get('per_gateway', '')
            net.static = request.POST.get('static', '')
            net.static_routes = request.POST.get('static_routes', '')
            net.subnet_mask = request.POST.get('subnet_mask', '')
            net.save()
            asset_info.networking.add(net)

            group = AssetGroup()
            group_id = request.POST.getlist('group')
            for item in group_id:
                group = AssetGroup.objects.get(id=int(item))
                asset_info.group.add(group)

        except ServerError:
            res['flag'] = 'false'
            res['content'] = error
        else:
            res['content'] = 'edit %s success' % hostname
            fileds = {
                "name": request.POST.get('name'),
                "hostname": request.POST.get('hostname'),
                "profile": request.POST.get('profile'),
                "gateway": request.POST.get('gateway'),
                "power_type": request.POST.get('power_type'),
                "power_address": request.POST.get('power_address'),
                "power_user": request.POST.get('power_username'),
                "power_pass": request.POST.get('power_password'),
                "interfaces": {
                    "eth0":{
                        "mac_address": request.POST.get('mac_address'),
                        "ip_address": request.POST.get('ip_address'),
                        "if_gateway": request.POST.get('per_gateway'),
                        "mtu": request.POST.get('mtu'),
                        "static": 1,
                    },
                }
            }

            data = json.dumps(fileds)
            select_proxy = get_object(Proxy, id=int(request.POST.get('proxy')))
            pro_username = select_proxy.username
            pro_password = select_proxy.password
            pro_url = select_proxy.url
            try:
                api = APIRequest('http://172.16.30.69:8100/v1.0/system/', 'test', '123456')
                result, code = api.req_put(data)
                # tk = Task()
                # tk.task_name = res['task_name']
                # tk.username = request.user.username
                # tk.status = res['status']
                # tk.url = res['link']
                # tk.start_time = datetime.datetime.now()
            except Exception,e:
                    error = e
            else:
                if code == 200:
                    msg = result['messege']
                else:
                    error = result['messege']

    return my_render('assetManage/asset_edit.html', locals(), request)


@require_role('user')
def asset_list(request):
    """
    asset list view
    """
    header_title, path1, path2 = u'查看资产', u'资产管理', u'查看资产'
    username = request.user.username
    user_perm = request.session['role_id']
    idc_all = IDC.objects.filter()
    asset_group_all = AssetGroup.objects.all()
    asset_types = ASSET_TYPE
    asset_status = ASSET_STATUS
    idc_name = request.GET.get('idc', '')
    group_name = request.GET.get('group', '')
    asset_type = request.GET.get('asset_type', '')
    status = request.GET.get('status', '')
    keyword = request.GET.get('keyword', '')
    export = request.GET.get("export", False)
    group_id = request.GET.get("group_id", '')
    idc_id = request.GET.get("idc_id", '')
    asset_id_all = request.GET.getlist("id", '')

    if group_id:
        group = get_object(AssetGroup, id=group_id)
        if group:
            asset_find = Asset.objects.filter(group=group)
    elif idc_id:
        idc = get_object(IDC, id=idc_id)
        if idc:
            asset_find = Asset.objects.filter(idc=idc)
    else:
        if user_perm != 0:
            asset_find = Asset.objects.all()
        else:
            asset_id_all = []
            user = get_object(User, username=username)
            asset_perm = get_group_user_perm(user) if user else {'asset': ''}
            user_asset_perm = asset_perm['asset'].keys()
            for asset in user_asset_perm:
                asset_id_all.append(asset.id)
            asset_find = Asset.objects.filter(pk__in=asset_id_all)
            asset_group_all = list(asset_perm['asset_group'])

    if idc_name:
        asset_find = asset_find.filter(idc__name__contains=idc_name)

    if group_name:
        asset_find = asset_find.filter(group__name__contains=group_name)

    if asset_type:
        asset_find = asset_find.filter(asset_type__contains=asset_type)

    if status:
        asset_find = asset_find.filter(status__contains=status)

    if keyword:
        asset_find = asset_find.filter(
            Q(hostname__contains=keyword) |
            Q(other_ip__contains=keyword) |
            Q(ip__contains=keyword) |
            Q(remote_ip__contains=keyword) |
            Q(comment__contains=keyword) |
            Q(username__contains=keyword) |
            Q(group__name__contains=keyword) |
            Q(cpu__contains=keyword) |
            Q(memory__contains=keyword) |
            Q(disk__contains=keyword) |
            Q(brand__contains=keyword) |
            Q(cabinet__contains=keyword) |
            Q(sn__contains=keyword) |
            Q(system_type__contains=keyword) |
            Q(system_version__contains=keyword))

    if export:
        if asset_id_all:
            asset_find = []
            for asset_id in asset_id_all:
                asset = get_object(Asset, id=asset_id)
                if asset:
                    asset_find.append(asset)
        s = write_excel(asset_find)
        if s[0]:
            file_name = s[1]
        smg = u'excel文件已生成，请点击下载!'
        return my_render('assetManage/asset_excel_download.html', locals(), request)
    assets_list, p, assets, page_range, current_page, show_first, show_end = pages(asset_find, request)
    if user_perm != 0:
        return my_render('assetManage/asset_list.html', locals(), request)
    else:
        return my_render('assetManage/asset_cu_list.html', locals(), request)


@require_role('admin')
def asset_start_up(request):
    data = {}
    if request.method == 'POST':
        select_ids = request.POST.getlist('asset_id_all')
        asset_list = []
        for item in select_ids:
            asset = get_object(Asset, id=int(item))
            asset_list.append(asset)
        proxy = asset_list[0].proxy
        username = proxy.username
        password = proxy.password
        api = APIRequest('http://172.16.30.69:8100/v1.0/system/action', 'test', '123456')
        result, codes = api.req_post(data)
        logger.debug("result:%s   codes:%s"%(result,codes))
        return HttpResponse(json.dumps(result), content_type='application/json')


@require_role('admin')
def asset_restart(request):
    data = {}
    if request.method == 'POST':
        select_ids = request.POST.getlist('asset_id_all')
        asset_list = []
        for item in select_ids:
            asset = get_object(Asset, id=int(item))
            asset_list.append(asset)
        proxy = asset_list[0].proxy
        username = proxy.username
        password = proxy.password
        api = APIRequest('http://172.16.30.69:8100/v1.0/system/action', 'test', '123456')
        result, codes = api.req_post(data)
        logger.debug("result:%s   codes:%s"%(result,codes))
        return HttpResponse(json.dumps(result), content_type='application/json')


@require_role('admin')
def asset_shutdown(request):
    data = {}
    if request.method == 'POST':
        select_ids = request.POST.getlist('asset_id_all')
        asset_list = []
        for item in select_ids:
            asset = get_object(Asset, id=int(item))
            asset_list.append(asset)
        proxy = asset_list[0].proxy
        username = proxy.username
        password = proxy.password
        api = APIRequest('http://172.16.30.69:8100/v1.0/system/action', 'test', '123456')
        result, codes = api.req_post(data)
        logger.debug("result:%s   codes:%s"%(result,codes))
        return HttpResponse(json.dumps(result), content_type='application/json')


@require_role('admin')
@user_operator_record
def asset_edit_batch(request, res, *args):
    res['operator'] = res['content'] = '修改主机'
    af = AssetForm()
    name = request.user.username
    asset_group_all = AssetGroup.objects.all()

    if request.method == 'POST':
        env = request.POST.get('env', '')
        idc_id = request.POST.get('idc', '')
        port = request.POST.get('port', '')
        use_default_auth = request.POST.get('use_default_auth', '')
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        group = request.POST.getlist('group', [])
        cabinet = request.POST.get('cabinet', '')
        comment = request.POST.get('comment', '')
        asset_id_all = unicode(request.GET.get('asset_id_all', ''))
        asset_id_all = asset_id_all.split(',')
        for asset_id in asset_id_all:
            alert_list = []
            asset = get_object(Asset, id=asset_id)
            if asset:
                if env:
                    if asset.env != env:
                        asset.env = env
                        alert_list.append([u'运行环境', asset.env, env])
                if idc_id:
                    idc = get_object(IDC, id=idc_id)
                    name_old = asset.idc.name if asset.idc else u''
                    if idc and idc.name != name_old:
                        asset.idc = idc
                        alert_list.append([u'机房', name_old, idc.name])
                if port:
                    if unicode(asset.port) != port:
                        asset.port = port
                        alert_list.append([u'端口号', asset.port, port])

                if use_default_auth:
                    if use_default_auth == 'default':
                        asset.use_default_auth = 1
                        asset.username = ''
                        asset.password = ''
                        alert_list.append([u'使用默认管理账号', asset.use_default_auth, u'默认'])
                    elif use_default_auth == 'user_passwd':
                        asset.use_default_auth = 0
                        asset.username = username
                        password_encode = CRYPTOR.encrypt(password)
                        asset.password = password_encode
                        alert_list.append([u'使用默认管理账号', asset.use_default_auth, username])
                if group:
                    group_new, group_old, group_new_name, group_old_name = [], asset.group.all(), [], []
                    for group_id in group:
                        g = get_object(AssetGroup, id=group_id)
                        if g:
                            group_new.append(g)
                    if not set(group_new) < set(group_old):
                        group_instance = list(set(group_new) | set(group_old))
                        for g in group_instance:
                            group_new_name.append(g.name)
                        for g in group_old:
                            group_old_name.append(g.name)
                        asset.group = group_instance
                        alert_list.append([u'主机组', ','.join(group_old_name), ','.join(group_new_name)])
                if cabinet:
                    if asset.cabinet != cabinet:
                        asset.cabinet = cabinet
                        alert_list.append([u'机柜号', asset.cabinet, cabinet])
                if comment:
                    if asset.comment != comment:
                        asset.comment = comment
                        alert_list.append([u'备注', asset.comment, comment])
                asset.save()
                res['content'] += '[%s]   ' % asset.name
            if alert_list:
                recode_name = unicode(name) + ' - ' + u'批量'
                AssetRecord.objects.create(asset=asset, username=recode_name, content=alert_list)
        return my_render('assetManage/asset_update_status.html', locals(), request)

    return my_render('assetManage/asset_edit_batch.html', locals(), request)


@require_role('admin')
def asset_detail(request):
    """
    Asset detail view
    """
    header_title, path1, path2 = u'主机详细信息', u'资产管理', u'主机详情'
    asset_id = request.GET.get('id', '')
    asset = get_object(Asset, id=asset_id)
    perm_info = get_group_asset_perm(asset)
    log = Log.objects.filter(host=asset.name)
    if perm_info:
        user_perm = []
        for perm, value in perm_info.items():
            if perm == 'user':
                for user, role_dic in value.items():
                    user_perm.append([user, role_dic.get('role', '')])
            elif perm == 'user_group' or perm == 'rule':
                user_group_perm = value
    print perm_info

    asset_record = AssetRecord.objects.filter(asset=asset).order_by('-alert_time')

    return my_render('assetManage/asset_detail.html', locals(), request)


@require_role('admin')
@user_operator_record
def asset_update(request,res, *args):
    """
    Asset update host info via ansible view
    """
    res['operator'] = '更新主机'
    asset_id = request.GET.get('id', '')
    asset = get_object(Asset, id=asset_id)
    name = request.user.username
    if not asset:
        res['flag'] = 'false'
        res['content'] = '主机[%s]不存在' % asset.name
        return HttpResponseRedirect(reverse('asset_detail')+'?id=%s' % asset_id)
    else:
        asset_ansible_update([asset], name)
        res['content'] = '更新主机[%s]' % asset.name
    return HttpResponseRedirect(reverse('asset_detail')+'?id=%s' % asset_id)


@require_role('admin')
@user_operator_record
def asset_update_batch(request,res,*args):
    res['operator'] = res['content'] = '批量更新主机'
    if request.method == 'POST':
        arg = request.GET.get('arg', '')
        name = unicode(request.user.username) + ' - ' + u'自动更新'
        if arg == 'all':
            asset_list = Asset.objects.all()
        else:
            asset_list = []
            asset_id_all = unicode(request.POST.get('asset_id_all', ''))
            asset_id_all = asset_id_all.split(',')
            for asset_id in asset_id_all:
                asset = get_object(Asset, id=asset_id)
                if asset:
                    asset_list.append(asset)
        asset_ansible_update(asset_list, name)
        for asset in asset_list:
            res['content'] += ' [%s] '% asset.name
        return HttpResponse(u'批量更新成功!')
    return HttpResponse(u'批量更新成功!')


@require_role('admin')
@user_operator_record
def idc_add(request,res, *args):
    """
    IDC add view
    """
    header_title, path1, path2 = '添加IDC', '资产管理', '添加IDC'
    res['operator'] = path2
    if request.method == 'POST':
        idc_form = IdcForm(request.POST)
        if idc_form.is_valid():
            idc_name = idc_form.cleaned_data['name']

            if IDC.objects.filter(name=idc_name):
                emg = '添加失败, 此IDC [%s] 已存在!' % idc_name
                res['flag'] = 'false'
                res['content'] = emg
                return my_render('assetManage/idc_add.html', locals(), request)
            else:
                idc_form.save()
                smg = 'IDC: [%s]添加成功' % idc_name
                res['content'] = smg
            return HttpResponseRedirect(reverse('idc_list'))
    else:
        idc_form = IdcForm()
    return my_render('assetManage/idc_add.html', locals(), request)


@require_role('admin')
def idc_list(request):
    """
    IDC list view
    """
    header_title, path1, path2 = u'查看IDC', u'资产管理', u'查看IDC'
    posts = IDC.objects.all()
    keyword = request.GET.get('keyword', '')
    if keyword:
        posts = IDC.objects.filter(Q(name__contains=keyword) | Q(comment__contains=keyword))
    else:
        posts = IDC.objects.exclude(name='ALL').order_by('id')
    contact_list, p, contacts, page_range, current_page, show_first, show_end = pages(posts, request)
    return my_render('assetManage/idc_list.html', locals(), request)


@require_role('admin')
@user_operator_record
def idc_edit(request, res, *args):
    """
    IDC edit view
    """
    header_title, path1, path2 = '编辑IDC', '资产管理', '编辑IDC'
    res['operator'] = path2
    idc_id = request.GET.get('id', '')
    idc = get_object(IDC, id=idc_id)
    if request.method == 'POST':
        idc_form = IdcForm(request.POST, instance=idc)
        if idc_form.is_valid():
            res['content'] = '编辑IDC[%s]' % idc.name
            idc_form.save()
            return HttpResponseRedirect(reverse('idc_list'))
    else:
        idc_form = IdcForm(instance=idc)
        return my_render('assetManage/idc_edit.html', locals(), request)


@require_role('admin')
@user_operator_record
def idc_del(request,res, *args):
    """
    IDC delete view
    """
    res['operator'] = res['content'] = '删除机房'
    idc_ids = request.GET.get('id', '')
    idc_id_list = idc_ids.split(',')

    for idc_id in idc_id_list:
        idc = IDC.objects.get(id=idc_id)
        res['content'] += '  [%s]  ' % idc.name

    return HttpResponseRedirect(reverse('idc_list'))


@require_role('admin')
@user_operator_record
def asset_upload(request,res, *args):
    """
    Upload asset excel file view
    """
    res['operator'] = '批量添加主机'
    if request.method == 'POST':
        excel_file = request.FILES.get('file_name', '')
        ret, asset_name_list = excel_to_db(excel_file)
        if ret:
            smg = u'批量添加成功'
            for item in asset_name_list:
                res['content'] += " [%s] " % item

        else:
            emg = u'批量添加失败,请检查格式.'
            res['flag'] = 'false'
            res['content'] = emg
    return my_render('assetManage/asset_add_batch.html', locals(), request)
