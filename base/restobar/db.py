import psycopg2
import configparser
import time

config = configparser.ConfigParser()
config.read('config.ini')

db_name = config['BASE']['DB_NAME']
db_user = config['BASE']['DB_USER']
db_pass = config['BASE']['DB_PASS']
db_host = config['BASE']['DB_HOST']
db_port = config['BASE']['DB_PORT']

def __conectarse():
    try:
        # nos conectamos a la bd
        cnx = psycopg2.connect(database=db_name, user=db_user,
                                password=db_pass, host=db_host, port=db_port)
        return cnx
    except (Exception, psycopg2.Error) as error:
        print("Error fetching data from PostgreSQL table", error)


def r_update_venta_pgsql(estado, ext_id, id):
    try:
        cnx = __conectarse()
        cursor = cnx.cursor()
        cursor.execute(
            "UPDATE gulash.ventas SET observaciones_declaracion = %s, estado_declaracion=%s WHERE id_venta = %s", (ext_id, estado, id))
        cnx.commit() #Guarda los cambios en la bd
    finally:
        # closing database connection
        if (cnx):
            cursor.close()
            cnx.close()


def r_read_empresa_pgsql():
    try:
        cnx = __conectarse()
        cursor = cnx.cursor()
        cursor.execute("SELECT * FROM gulash.parametros WHERE descripcion = 'EFACTUR URL'")
        url = cursor.fetchone()   
        cursor.execute("SELECT * FROM gulash.parametros WHERE descripcion = 'EFACTUR EMPRESA'")
        token = cursor.fetchone()   
        return [url[2], token[2]]
    finally:
        # closing database connection
        if (cnx):
            cursor.close()
            cnx.close()


def r_update_anulados_pgsql(estado, estado_anulado, ext_id, id):
    try:
        cnx = __conectarse()
        cursor = cnx.cursor()
        cursor.execute(
            "UPDATE gulash.ventas SET estado_declaracion=%s, estado_declaracion_anulado=%s, observaciones_declaracion=%s WHERE id_venta = %s", (estado, estado_anulado, ext_id, id))
        cnx.commit()
    finally:
        # closing database connection
        if (cnx):
            cursor.close()
            cnx.close()


def r_update_no_200(estado, id):
    try:
        cnx = __conectarse()
        cursor = cnx.cursor()
        cursor.execute(
            "UPDATE gulash.ventas SET estado_declaracion = %s WHERE id_venta = %s", (estado, id))
        cnx.commit()
    finally:
        # closing database connection
        if (cnx):
            cursor.close()
            cnx.close()