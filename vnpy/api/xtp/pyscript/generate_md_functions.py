# encoding: UTF-8

__author__ = 'CHENXY'

from string import join

from xtp_struct_common import structDict as structDict2
from xtp_struct_quote import structDict

structDict.update(structDict2)


# ----------------------------------------------------------------------
def replace_tabs(f):
    """把Tab用4个空格替代"""
    l = []
    for line in f:
        line = line.replace('\t', '    ')
        l.append(line)
    return l


def process_callback(line):
    original_line = line
    line = line.replace('    virtual void ', '')  # 删除行首的无效内容
    line = line.replace('{};\n', '')  # 删除行尾的无效内容

    content = line.split('(')
    cb_name = content[0]  # 回调函数名称
    cb_name = cb_name.strip()

    cb_args = content[1]  # 回调函数参数
    if cb_args[-1] == ' ':
        cb_args = cb_args.replace(') ', '')
    else:
        cb_args = cb_args.replace(')', '')

    cb_args_list = cb_args.split(', ')  # 将每个参数转化为列表

    cb_args_type_list = []
    cb_args_value_list = []

    for arg in cb_args_list:  # 开始处理参数
        content = arg.split(' ')
        if len(content) > 1:
            cb_args_type_list.append(content[0])  # 参数类型列表
            cb_args_value_list.append(content[1])  # 参数数据列表

    create_task(cb_name, cb_args_type_list, cb_args_value_list, original_line)
    create_process(cb_name, cb_args_type_list, cb_args_value_list)

    # 生成.h文件中的process部分
    process_line = 'void process' + cb_name[2:] + '(Task *task);\n'
    f_header_process.write(process_line)
    f_header_process.write('\n')

    # 生成.h文件中的on部分
    # if 'OnRspError' in cbName:
    # on_line = 'virtual void on' + cbName[2:] + '(dict error, int id, bool last) {};\n'
    # elif 'OnRsp' in cbName:
    # on_line = 'virtual void on' + cbName[2:] + '(dict data, dict error, int id, bool last) {};\n'
    # elif 'OnRtn' in cbName:
    # on_line = 'virtual void on' + cbName[2:] + '(dict data) {};\n'
    # elif 'OnErrRtn' in cbName:
    # on_line = 'virtual void on' + cbName[2:] + '(dict data, dict error) {};\n'
    # else:
    # on_line = ''

    if line.count('*') == 1:
        on_line = 'virtual void on' + cb_name[2:] + '(dict data) {};\n'
    elif line.count('*') == 2:
        on_line = 'virtual void on' + cb_name[2:] + '(dict data, dict error, bool last) {};\n'
    elif line.count('*') == 0:
        on_line = 'virtual void on' + cb_name[2:] + '() {};\n'
    else:
        on_line = ''

    f_header_on.write(on_line)
    f_header_on.write('\n')

    # 生成封装部分
    create_wrap(cb_name, line)


# ----------------------------------------------------------------------
def create_wrap(cb_name, line):
    """在Python封装段代码中进行处理"""
    # 生成.h文件中的on部分
    # if 'OnRspError' in cbName:
    # on_line = 'virtual void on' + cbName[2:] + '(dict error, int id, bool last)\n'
    # override_line = '("on' + cbName[2:] + '")(error, id, last);\n'
    # elif 'OnRsp' in cbName:
    # on_line = 'virtual void on' + cbName[2:] + '(dict data, dict error, int id, bool last)\n'
    # override_line = '("on' + cbName[2:] + '")(data, error, id, last);\n'
    # elif 'OnRtn' in cbName:
    # on_line = 'virtual void on' + cbName[2:] + '(dict data)\n'
    # override_line = '("on' + cbName[2:] + '")(data);\n'
    # elif 'OnErrRtn' in cbName:
    # on_line = 'virtual void on' + cbName[2:] + '(dict data, dict error)\n'
    # override_line = '("on' + cbName[2:] + '")(data, error);\n'
    # else:
    # on_line = ''

    if line.count('*') == 1:
        on_line = 'virtual void on' + cb_name[2:] + '(dict data)\n'
        override_line = '("on' + cb_name[2:] + '")(data);\n'
    elif line.count('*') == 2:
        on_line = 'virtual void on' + cb_name[2:] + '(dict data, dict error, bool last)\n'
        override_line = '("on' + cb_name[2:] + '")(data, error, last);\n'
    elif line.count('*') == 0:
        on_line = 'virtual void on' + cb_name[2:] + '()\n'
        override_line = '("on' + cb_name[2:] + '")();\n'
    else:
        on_line = ''

    if on_line is not '':
        f_wrap.write(on_line)
        f_wrap.write('{\n')
        f_wrap.write('    try\n')
        f_wrap.write('    {\n')
        f_wrap.write('        this->get_override' + override_line)
        f_wrap.write('    }\n')
        f_wrap.write('    catch (error_already_set const &)\n')
        f_wrap.write('    {\n')
        f_wrap.write('        PyErr_Print();\n')
        f_wrap.write('    }\n')
        f_wrap.write('};\n')
        f_wrap.write('\n')


def create_task(cb_name, cb_args_type_list, cb_args_value_list, original_line):
    # 从回调函数生成任务对象，并放入队列
    func_line = original_line.replace('            virtual void ', 'void ' + apiName + '::')
    func_line = func_line.replace('{};', '')

    f_task.write(func_line)
    f_task.write('{\n')
    f_task.write("    Task* task = new Task();\n")

    f_task.write("    task->task_name = " + cb_name.upper() + ";\n")

    # define常量
    global define_count
    f_define.write("#define " + cb_name.upper() + ' ' + str(define_count) + '\n')
    define_count = define_count + 1

    # switch段代码
    f_switch.write("case " + cb_name.upper() + ':\n')
    f_switch.write("{\n")
    f_switch.write("    this->" + cb_name.replace('On', 'process') + '(task);\n')
    f_switch.write("    break;\n")
    f_switch.write("}\n")
    f_switch.write("\n")

    for i, type_ in enumerate(cb_args_type_list):
        if type_ == 'int':
            f_task.write("    task->task_id = " + cb_args_value_list[i] + ";\n")
        elif type_ == 'bool':
            f_task.write("    task->task_last = " + cb_args_value_list[i] + ";\n")
        elif 'XTPRI' in type_:
            f_task.write("\n")
            f_task.write("    if (error_info)\n")
            f_task.write("    {\n")
            f_task.write("        " + type_ + ' *task_error = new ' + type_ + '();\n')
            f_task.write("        " + '*task_error = ' + cb_args_value_list[i] + ';\n')
            f_task.write("        task->task_error = task_error;\n")
            f_task.write("    }\n")
            f_task.write("\n")
        else:
            f_task.write("\n")
            f_task.write("    if (" + cb_args_value_list[i][1:] + ")\n")
            f_task.write("    {\n")

            f_task.write("        " + type_ + ' *task_data = new ' + type_ + '();\n')
            f_task.write("        " + '*task_data = ' + cb_args_value_list[i] + ';\n')
            f_task.write("        task->task_data = task_data;\n")
            f_task.write("    }\n")

    f_task.write("    this->task_queue.push(task);\n")
    f_task.write("};\n")
    f_task.write("\n")


def create_process(cb_name, cb_args_type_list, cb_args_value_list):
    # 从队列中提取任务，并转化为python字典
    f_process.write("void " + apiName + '::' + cb_name.replace('On', 'process') + '(Task *task)' + "\n")
    f_process.write("{\n")
    f_process.write("    PyLock lock;\n")

    on_args_list = []

    for i, type_ in enumerate(cb_args_type_list):
        if 'XTPRI' in type_:
            f_process.write("    " + "dict error;\n")
            f_process.write("    if (task->task_error)\n")
            f_process.write("    {\n")
            f_process.write("        " + type_ + ' *task_error = (' + type_ + '*) task->task_error;\n')

            struct = structDict[type_]
            for key in struct.keys():
                f_process.write("        " + 'error["' + key + '"] = task_error->' + key + ';\n')

            f_process.write("        delete task->task_error;\n")
            f_process.write("    }\n")
            f_process.write("\n")

            on_args_list.append('error')

        elif type_ in structDict:
            f_process.write("    " + "dict data;\n")
            f_process.write("    if (task->task_data)\n")
            f_process.write("    {\n")
            f_process.write("        " + type_ + ' *task_data = (' + type_ + '*) task->task_data;\n')

            struct = structDict[type_]
            for key, value in struct.items():
                if value != 'enum':
                    f_process.write("        " + 'data["' + key + '"] = task_data->' + key + ';\n')
                else:
                    f_process.write("        " + 'data["' + key + '"] = (int)task_data->' + key + ';\n')

            f_process.write("        delete task->task_data;\n")
            f_process.write("    }\n")
            f_process.write("\n")

            on_args_list.append('data')

        elif type_ == 'bool':
            on_args_list.append('task->task_last')

        elif type_ == 'int':
            on_args_list.append('task->task_id')

    on_args = join(on_args_list, ', ')
    f_process.write('    this->' + cb_name.replace('On', 'on') + '(' + on_args + ');\n')
    f_process.write('    delete task;\n')

    f_process.write("};\n")
    f_process.write("\n")


def process_function(line):
    line = line.replace('    virtual int ', '')  # 删除行首的无效内容
    line = line.replace(') = 0;\n', '')  # 删除行尾的无效内容

    content = line.split('(')
    fc_name = content[0]  # 回调函数名称

    fc_args = content[1]  # 回调函数参数
    fc_args = fc_args.replace(')', '')

    fc_args_list = fc_args.split(', ')  # 将每个参数转化为列表

    fc_args_type_list = []
    fc_args_value_list = []

    for arg in fc_args_list:  # 开始处理参数
        content = arg.split(' ')
        if len(content) > 1:
            fc_args_type_list.append(content[0])  # 参数类型列表
            fc_args_value_list.append(content[1])  # 参数数据列表

    if len(fc_args_type_list) > 0 and fc_args_type_list[0] in structDict:
        create_function(fc_name, fc_args_type_list, fc_args_value_list)

    # 生成.h文件中的主动函数部分
    if 'Req' in fc_name:
        req_line = 'int req' + fc_name[3:] + '(dict req, int nRequestID);\n'
        f_header_function.write(req_line)
        f_header_function.write('\n')


def create_function(fcName, fcArgsTypeList, fcArgsValueList):
    type_ = fcArgsTypeList[0]
    struct = structDict[type_]

    f_function.write('int QuoteApi::req' + fcName[3:] + '(dict req, int nRequestID)\n')
    f_function.write('{\n')
    f_function.write('    ' + type_ + ' myreq = ' + type_ + '();\n')
    f_function.write('    memset(&myreq, 0, sizeof(myreq));\n')

    line = ''
    for key, value in struct.items():
        if value == 'string':
            line = '    getString(req, "' + key + '", myreq.' + key + ');\n'
        elif value == 'char':
            line = '    getChar(req, "' + key + '", &myreq.' + key + ');\n'
        elif value == 'int':
            line = '    getInt(req, "' + key + '", &myreq.' + key + ');\n'
        elif value == 'double':
            line = '    getDouble(req, "' + key + '", &myreq.' + key + ');\n'
        f_function.write(line)

    f_function.write('    int i = this->api->' + fcName + '(&myreq, nRequestID);\n')
    f_function.write('    return i;\n')

    f_function.write('};\n')
    f_function.write('\n')


#########################################################
apiName = 'QuoteApi'

f_cpp = open('xtp_quote_api.h', 'r')
f_task = open('xtp_md_task.cpp', 'w')
f_process = open('xtp_md_process.cpp', 'w')
f_function = open('xtp_md_function.cpp', 'w')
f_define = open('xtp_md_define.cpp', 'w')
f_switch = open('xtp_md_switch.cpp', 'w')
f_header_process = open('xtp_md_header_process.h', 'w')
f_header_on = open('xtp_md_header_on.h', 'w')
f_header_function = open('xtp_md_header_function.h', 'w')
f_wrap = open('xtp_md_wrap.cpp', 'w')

define_count = 1

for line in replace_tabs(f_cpp):
    if "virtual void On" in line:
        process_callback(line)
    elif "virtual int" in line:
        process_function(line)

f_cpp.close()
f_task.close()
f_process.close()
f_function.close()
f_switch.close()
f_define.close()
f_header_process.close()
f_header_on.close()
f_header_function.close()
f_wrap.close()

print 'md functions done'
