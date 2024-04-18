import math
import json
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from flask_bcrypt import Bcrypt
from flask import (
    Flask,
    render_template,
    request,
    url_for,
    redirect,
    session,
    make_response,
)

from dbOperations import *

app = Flask(__name__)
# 将Flask-Bcrypt集成到应用程序中
bcrypt = Bcrypt(app)
app.secret_key = "abcdefgh!@#$%"

# 先建立数据库连接
conn = openMyDatabase()


# 生成随机验证码
def generate_captcha():
    # 生成随机验证码字符串，长度为4
    captcha_text = "".join(
        random.choices(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", k=4
        )
    )

    # 创建图像
    width, height = 130, 40
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    # 生成随机干扰线
    for i in range(10):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line((x1, y1, x2, y2), fill=(0, 0, 0))

    # 生成随机干扰点
    for i in range(100):
        draw.point(
            [random.randint(0, width), random.randint(0, height)], fill=(0, 0, 0)
        )

    # 加载字体文件
    font_path = "./static/font/Nereus/normal/NereusItalic-Bold.ttf"
    font_size = 50
    font = ImageFont.truetype(font_path, font_size)
    # 获取验证码文本的宽度和高度
    text_width, text_height = draw.textsize(captcha_text, font)
    # 计算文本位于图像中央的坐标
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # 在图像上绘制验证码
    draw.text((x, y - 6), captcha_text, fill=(0, 0, 0), font=font)

    # 将图像保存到内存中
    image_io = BytesIO()
    image.save(image_io, "PNG")
    image_io.seek(0)

    return captcha_text, image_io


# 检查用户是否已登录
def CheckLogin():
    if "username" in session:
        return True
    else:
        return False


# 验证用输入的用户名和密码是否正确，正确返回True，错误返回False
def verifyLogin(username, password):
    cursor = conn.cursor()
    # 从数据库中查询哈希密码
    sql = "select password from user where username = ?;"
    # 执行sql语句
    cursor.execute(sql, (username,))
    # 获取结果
    result = cursor.fetchall()
    # 关闭游标
    cursor.close()
    # 如果用户名不存在
    if len(result) == 0:
        return False
    # 如果用户名存在
    else:
        # 获取数据库中的哈希密码
        hashed_password = result[0]["password"]
        # 验证密码
        if bcrypt.check_password_hash(hashed_password, password):
            return True
        else:
            return False


@app.route("/captcha")
def captcha():
    # 生成验证码
    captcha_text, image_io = generate_captcha()
    # 将验证码的全大写和全小写形式都存入session中
    session["captcha_upper"] = captcha_text.upper()
    session["captcha_lower"] = captcha_text.lower()
    # 将图像返回给浏览器
    response = make_response(image_io.read())
    response.headers["Content-Type"] = "image/png"
    return response


@app.route("/login", methods=["POST", "GET"])
def login():
    # 正常访问该路由时访问类型为GET，直接返回登录页面即可
    if request.method == "GET":
        return render_template("login.html")
    # 当访问类型为POST时，需要处理登录逻辑
    if request.method == "POST":
        # 获取用户输入的验证码
        user_captcha = request.form.get("captcha")
        # 如果用户输入的验证码与session中存储的验证码大小写均不一致
        if user_captcha != session.get("captcha_upper") and user_captcha != session.get(
            "captcha_lower"
        ):
            # 验证失败
            return render_template("login.html", error_message="验证码错误！")
        # 如果用户输入的验证码正确，则继续验证用户名和密码是否正确
        if verifyLogin(request.form["username"], request.form["password"]):
            # 登录成功
            # 将用户名存入session中
            session["username"] = request.form["username"]
            return redirect(url_for("home"))
        else:
            # 登录失败
            error_message = "用户名或密码错误！"
            return render_template("login.html", error_message=error_message)


@app.route("/", methods=["GET"])
def home():
    # 检查是否登录
    if not CheckLogin():
        return redirect(url_for("login"))
    # 查询条件，需要返回！
    select_condition = {}
    # 设计sql中的where字句
    strWhere = []
    # 第一个查询条件为学生姓名，name
    if "name" in request.args:
        # 取出数据
        name = request.args["name"]
        # 存入select_condition字典
        select_condition["name"] = name
        # 如果name字段不为空
        if name != "":
            strWhere.append("s.name like '%%%s%%'" % name)
    # 第二个查询条件为学生学号，ID
    if "id" in request.args:
        # 取出数据
        ID = request.args["id"]
        # 存入select_condition字典
        select_condition["id"] = ID
        if ID != "":
            strWhere.append("s.id like '%%%s%%'" % ID)

    # 查询总的学生信息数量
    sql = """SELECT count(*) count FROM student s"""
    # 如果输入了查询条件
    if len(strWhere) > 0:
        sql = sql + " where " + " and ".join(strWhere) + ";"
    # 执行sql语句并将结果保存到变量中
    count, _ = selectData(conn, sql)

    # 初始化total_page_number变量，当前总共有几页的数据
    total_page_number = math.ceil(count[0]["count"] / 9 - 1) + 1
    # 初始化page_number变量，表示传给模板的是第几页的数据，默认传第1页的数据
    page_number = "1"
    # 如果参数中含有指定页面的参数
    if "page" in request.args:
        page = request.args["page"]
        # 如果传的参数不合法
        if int(page) <= 0:
            # 将page_number设为1
            page_number = 1
            # 将page设为空，返回第1页数据即可
            page = ""
        # 如果传的参数不合法
        elif int(page) > total_page_number:
            # 将page赋值成最大页数
            page = str(total_page_number)
        if page != "":
            page_number = page
            # 返回第page页的学生信息
            sql = """SELECT s.*,p.name profession_name
                     FROM student s INNER JOIN profession p 
                     ON s.profession_id = p.id
                     %s
                     ORDER BY s.id
                     LIMIT 9 %s;""" % (
                ("where " + " and ".join(strWhere)) if (len(strWhere) > 0) else "",
                "OFFSET " + str(9 * (int(page) - 1)) if (int(page) > 0) else "",
            )
        else:
            # 返回第1页的学生信息
            sql = """SELECT s.*,p.name profession_name
                     FROM student s INNER JOIN profession p 
                     ON s.profession_id = p.id
                     %s
                     ORDER BY s.id
                     LIMIT 9;""" % (
                ("where " + " and ".join(strWhere)) if (len(strWhere) > 0) else ""
            )
    else:
        # 若参数中未含有指定页面的参数，则默认返回第1页的学生信息
        sql = """SELECT s.*,p.name profession_name
                 FROM student s INNER JOIN profession p 
                 ON s.profession_id = p.id
                 %s
                 ORDER BY s.id
                 LIMIT 9;""" % (
            ("where " + " and ".join(strWhere)) if (len(strWhere) > 0) else ""
        )
    # 执行sql语句并将结果保存到变量中
    students, fields = selectData(conn, sql)

    # 获取模板名参数
    if "template" in request.args:
        template_name = request.args["template"]
        # 如果要返回的是update_index模板
        if template_name == "update_index":
            return render_template(
                "update_index.html",
                total_page_number=total_page_number,
                students=students,
                username=session["username"],
                page_number=page_number,
                select_condition=select_condition,
                fields=fields,
                # 将收到的updateAges参数（不解析！直接以json字符串的形式返回！）再传给模板，以便模板再将其传给js脚本中的updateAges变量
                # 此处用的是request.args.get()方法，当参数中不含updateAges时，该方法不会报异常并返回None，而如果用的是
                # request.args[]的话当参数updateAges不存在时会报异常！
                updateAges=request.args.get("updateAges"),
                # 如果没有error_message则向模板返回None
                error_message=request.args.get("error_message"),
            )
    else:
        # 默认返回的是index.html
        return render_template(
            "index.html",
            total_page_number=total_page_number,
            students=students,
            username=session["username"],
            page_number=page_number,
            select_condition=select_condition,
            error_message=request.args.get("error_message"),
        )


# 检查表单信息合法性
def checkInfoValid(info):
    if (
        len(info["id"]) != 12
        or (len(info["name"]) < 2 or len(info["name"]) > 4)
        or len(info["age"]) == 0
        or (int(info["age"]) < 12 or int(info["age"]) > 30)
        or len(info["origin"]) == 0
        or len(info["profession_id"]) == 0
    ):
        return False
    else:
        return True


@app.route("/add", methods=["GET", "post"])
def add():
    if not CheckLogin():
        return redirect(url_for("login"))
    # 动态查询表中的专业数据并显示
    professions, _ = selectData(conn, "select * from profession;")
    # 当正常访问该路由时的请求方式为GET，直接返回add页面
    if request.method == "GET":
        # 动态查询表中的专业数据并显示
        return render_template(
            "add.html", professions=professions, username=session["username"], info={}
        )
    # 当提交数据到该路由时请求方式为POST，此时需要在数据库中进行增操作
    if request.method == "POST":
        # 重复性检查
        sql = """select * from student where id=%s""" % request.form["id"]
        result, _ = selectData(conn, sql)
        # 先根据参数生成字典对象
        info = dict(
            id=request.form["id"],
            name=request.form["name"],
            sex=request.form["sex"],
            age=request.form["age"],
            origin=request.form["origin"],
            profession_id=request.form["profession_id"],
        )
        # 如果信息不合法
        if not checkInfoValid(info):
            return render_template(
                "add.html",
                error_message="信息不合法！",
                professions=professions,
                username=session["username"],
                info=info,
            )
        # 如果学号重复
        if len(result) > 0:
            error_message = "学号已存在！"
            return render_template(
                "add.html",
                error_message=error_message,
                professions=professions,
                username=session["username"],
                info=info,
            )
        # 插入到表中
        insertData(conn, info, "student")
        error_message = "新建成功！"
        return render_template(
            "add.html",
            error_message=error_message,
            professions=professions,
            username=session["username"],
            info=info,
        )


@app.route("/delete", methods=["GET"])
def delete():
    if not CheckLogin():
        return redirect(url_for("login"))
    # 如果是单个删除
    if "id" in request.args:
        ID = request.args["id"]
        if ID != "":
            deleteDataById(conn, ID, "student")
    # 如果是批量删除
    if "IDsArray" in request.args:
        # 将IDsArray从url中解析出来并将其转换为python列表
        IDsArray = json.loads(request.args["IDsArray"])
        if len(IDsArray) != 0:
            for ID in IDsArray:
                deleteDataById(conn, ID, "student")

    # 一定删除成功
    return redirect("/?error_message=删除成功！")


@app.route("/update", methods=["GET", "POST"])
def update():
    if not CheckLogin():
        return redirect(url_for("login"))
    # 将全部专业信息返回
    professions, _ = selectData(conn, "select * from profession;")

    # 当通过index页面的修改按钮访问时，需要将该学生的的当前信息返回给update页面
    if "id" in request.args:
        ID = request.args["id"]
        info, _ = selectData(conn, "select * from student where id = %s;" % ID)
        return render_template(
            "update.html",
            info=dict(info[0]),
            username=session["username"],
            professions=professions,
        )

    # 当从update页面提交数据到该路由时请求方式为POST，此时需要在数据库中进行更新操作
    if request.method == "POST":
        # 生成字典对象
        info = dict(
            id=request.form["id"],
            name=request.form["name"],
            sex=request.form["sex"],
            age=request.form["age"],
            origin=request.form["origin"],
            profession_id=request.form["profession_id"],
        )
        # 如果信息不合法
        if not checkInfoValid(info):
            return render_template(
                "update.html",
                error_message="信息不合法！",
                professions=professions,
                username=session["username"],
                info=info,
            )
        updateData(conn, info, "student")
        error_message = "修改成功！"
        return render_template(
            "update.html",
            error_message=error_message,
            professions=professions,
            username=session["username"],
            info=info,
        )

    # 当通过update_index页面的批量修改按钮访问时
    if "updateAges" in request.args:
        # 将updateAges从url中解析出来并将其转换为python字典
        updateAges = json.loads(request.args["updateAges"])
        print(updateAges)
        # 先遍历第一遍updateAges进行年龄的合法性检验
        for ID, new_age in updateAges.items():
            # 合法性检验
            if int(new_age) < 12 or int(new_age) > 30:
                error_message = "学生年龄必须介于12至30之间！修改失败！"
                return redirect(
                    "/?template=update_index&updateAges="
                    + request.args["updateAges"]
                    + "&error_message="
                    + error_message
                )
        # 合法性检验通过，第二遍遍历updateAges，更新数据库中对应的年龄信息
        for ID, new_age in updateAges.items():
            # 更新数据库中对应的年龄信息
            updateAgeById(conn, ID, new_age)
        # 全部修改成功
        error_message = "修改成功！"
        return redirect("/?template=update_index&error_message=" + error_message)


# 退出登录
@app.route("/logout", methods=["GET"])
def logout():
    if not CheckLogin():
        return redirect(url_for("login"))
    session.pop("username")
    return redirect(url_for("home"))


@app.route("/user_info", methods=["GET"])
def user_info():
    if not CheckLogin():
        return redirect(url_for("login"))
    return render_template("user_info.html", username=session["username"])


# 修改密码
@app.route("/change_password", methods=["POST"])
def change_password():
    if not CheckLogin():
        return redirect(url_for("login"))
    # 如果旧密码为空
    if request.form["old_password"] == "":
        return render_template(
            "user_info.html", error_message="旧密码不能为空！", username=session["username"]
        )
    # 如果新密码和确认密码为空
    if request.form["new_password"] == "" or request.form["confirmed_password"] == "":
        return render_template(
            "user_info.html",
            error_message="新密码或确认密码不能为空！",
            username=session["username"],
        )
    # 如果新密码和确认密码不一致
    if request.form["new_password"] != request.form["confirmed_password"]:
        return render_template(
            "user_info.html", error_message="两次输入的密码不一致！", username=session["username"]
        )
    # 如果新密码长度不符合要求
    if len(request.form["new_password"]) < 3 or len(request.form["new_password"]) > 15:
        return render_template(
            "user_info.html", error_message="新密码长度必须介于2到15之间！", username=session["username"]
        )
    # 如果旧密码不正确
    if not verifyLogin(session["username"], request.form["old_password"]):
        return render_template(
            "user_info.html", error_message="旧密码错误！", username=session["username"]
        )
    # 根据新密码生成新的哈希密码
    hashed_password = bcrypt.generate_password_hash(
        password=request.form["new_password"]
    ).decode("utf-8")
    # 更新数据库中的密码
    changePassword(conn, session["username"], hashed_password)
    # 修改成功，返回user_info页面
    return render_template(
        "user_info.html",
        error_message="修改成功！",
        username=session["username"],
    )


# 运行app
if __name__ == "__main__":
    # app.run("0.0.0.0",debug=True)
    app.run(debug=False, port=5000)
    # app.run()
