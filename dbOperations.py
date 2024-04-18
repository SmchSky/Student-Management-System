# -*- coding: utf-8 -*-
import sqlite3


def openMyDatabase():
    """
    打开指定的数据库
    """
    database = "./db/myTest_1.db"
    # 连接到数据库（如果路径下不存在数据库文件则会新创建一个）
    conn = sqlite3.connect(database, check_same_thread=False)
    # 以字典的形式返回结果
    conn.row_factory = sqlite3.Row
    # 返回数据库连接对象
    return conn


def closeMyDatabase(conn):
    conn.close()


def selectData(conn, sql):
    """
    在指定的数据库中执行sql查询
    """
    cursor = conn.cursor()
    cursor.execute(sql)
    fields = []  # 表中所有的字段
    # 获取表中所有的字段名称
    for column in cursor.description:
        # cursor.description[i][0] 表示表中第i+1列的列名
        fields.append(column[0])
    # 执行sql语句并返回查询结果
    result = cursor.fetchall()

    # # 输出查询结果（应该是某种类型的列表，类型由conn.row_factory指定，本app采用的是字典类型，所以可以视为字典类型的列表）
    # print(type(result))
    # for item in result:
    #     print(type(item))

    # 关闭游标
    cursor.close()
    return result, fields


def updateData(conn, data, tableName):
    """
    在指定的数据库中执行数据更新操作
    """
    cursor = conn.cursor()
    # 用于保存更改后的值
    values = []
    # 由于data为字典类型，list(data)是将data的所有键放进一个列表然后返回！而data中的所有值被省略了！
    # 键的列表，也就是字段名称的列表
    fieldNames = list(data)
    # 主键字段名
    keyName = fieldNames[0]
    # 为values赋值，但values中不包含主键的值！！！
    for v in fieldNames[1:]:
        values.append(data[v])
    # 生成一个方便设计后面sql语句的字符串
    colNameEqualsQuestionMark = []
    for colName in fieldNames[1:]:
        colNameEqualsQuestionMark.append("%s=?" % colName)
    # 设计update的sql语句
    sql = "update %s set %s where %s='%s';" % (
        tableName,
        ",".join(colNameEqualsQuestionMark),
        keyName,
        data[keyName],
    )
    # print(sql)
    cursor.execute(sql, values)
    # 提交事务
    conn.commit()
    # 关闭游标
    cursor.close()


def insertData(conn, data, tableName):
    cursor = conn.cursor()
    # 值的列表
    values = []
    # 键的列表，也就是字段名称的列表
    fieldNames = list(data)
    # 为值的列表赋值
    for v in fieldNames:
        values.append(data[v])
    # 设计该sql语句时使用了？占位符
    sql = "insert into %s (%s) values(%s);" % (
        tableName,
        ",".join(fieldNames),
        ",".join(["?"] * len(fieldNames)),
    )
    # print(sql)
    cursor.execute(sql, values)
    conn.commit()
    # 关闭游标
    cursor.close()


def deleteDataById(conn, ID, tableName):
    cursor = conn.cursor()
    # 设计sql语句
    sql = "delete from %s  where %s.id = ?" % (tableName, tableName)
    # print(sql)
    cursor.execute(sql, (ID,))
    conn.commit()
    # 关闭游标
    cursor.close()


def updateAgeById(conn, ID, new_age):
    cursor = conn.cursor()
    # 设计sql语句
    sql = "update student set age = ? where id = ?;"
    # 执行sql语句
    cursor.execute(sql, (new_age, ID))
    conn.commit()
    # 关闭游标
    cursor.close()


# 修改密码
def changePassword(conn, username, new_hashed_password):
    cursor = conn.cursor()
    # 设计sql语句
    sql = "update user set password=? where username = ?;"
    # 执行sql语句
    cursor.execute(sql, (new_hashed_password, username))
    # 提交事务
    conn.commit()
    # 关闭游标
    cursor.close()


# insertData({"id": 202100800133, "name": "宋铭印", "sex": "男", "age": 21, "origin": "济南", "profession_id": 4},
#            "student")
# updateData({"id": "202100800132", "profession_id": "3"}, "student")
# deleteDataById(202100800133, "student")
# deleteDataById(5, "profession")
