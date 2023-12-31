from flask import Flask, jsonify, request
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()
uri = os.getenv("URI")
user = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, password), database="neo4j")

app = Flask(__name__)


def get_employees(x, query='', querytype='', sort='', sortType=''):
    print(query)
    employees_data = "MATCH (m:Employee) RETURN m"
    if query == "name":
        employees_data = f"MATCH (m:Employee) WHERE m.name = '{querytype}' RETURN m"
    elif query == "surname":
        employees_data = f"MATCH (m:Employee) WHERE m.surname = '{querytype}' RETURN m"
    elif query == "position":
        employees_data = f"MATCH (m:Employee) WHERE m.position = '{querytype}' RETURN m"
    if sort == "name":
        if (sortType == "asc"):
            employees_data = f"MATCH (m:Employee) RETURN m ORDER BY m.name"
        if (sortType == "desc"):
            employees_data = f"MATCH (m:Employee) RETURN m ORDER BY m.name DESC"
    if sort == "surname":
        if (sortType == "asc"):
            employees_data = f"MATCH (m:Employee) RETURN m ORDER BY m.surname"
        if (sortType == "desc"):
            employees_data = f"MATCH (m:Employee) RETURN m ORDER BY m.surname DESC"
    if sort == "position":
        if (sortType == "asc"):
            employees_data = f"MATCH (m:Employee) RETURN m ORDER BY m.position"
        if (sortType == "desc"):
            employees_data = f"MATCH (m:Employee) RETURN m ORDER BY m.position DESC"
    result = x.run(employees_data).data()
    employees = [{'name': result['m']['name'],
                  'surname': result['m']['surname'], 'position': result['m']['position']} for result in result]
    return employees


def add_employee(tx, name, surname, position, department):
    exits = f"MATCH (m:Employee) WHERE m.name = '{name}' AND m.surname = '{surname}' RETURN m"
    result = tx.run(exits).data()
    if not result:
        query = "MATCH (d:Department {name: $department}) CREATE (e:Employee {name: $name, surname: $surname, position: $position})-[:WORKS_IN]->(d)"
        tx.run(query, name=name, surname=surname,
               position=position, department=department)
        return True
    else:
        return False


def update_employee(tx, id, name=None, surname=None, position=None, department=None):
    if name:
        query = "MATCH (n:Employee) WHERE id(n) = $internal_id SET n.name = $name"
        tx.run(query, internal_id=id, name=name)
    if surname:
        query = "MATCH (n:Employee) WHERE id(n) = $internal_id SET n.surname = $surname"
        tx.run(query, internal_id=id, surname=surname)
    if position:
        query = "MATCH (n:Employee) WHERE id(n) = $internal_id SET n.position = $position"
        tx.run(query, internal_id=id, position=position)
    if department:
        query = "MATCH (n:Employee) WHERE id(n) = $internal_id MATCH (n)-[r:WORKS_IN]->(d:Department) MATCH (d2:Department {name: $department}) DELETE r MERGE (n)-[:WORKS_IN]->(d2)"
        tx.run(query, internal_id=id, department=department)


def delete_employee(tx, id, new_id=None):
    if new_id:
        query = "MATCH (n:Employee) WHERE id(n) = $internal_id OPTIONAL MATCH (n)-[r:WORKS_IN]->(d:Department) OPTIONAL MATCH (n)-[r2:MANAGES]->(d2:Department) WITH n, d, d2 MATCH (n2:Employee) WHERE id(n2) = $new_internal_id MERGE (n2)-[:MANAGES]->(d2) DETACH DELETE n"
        tx.run(query, internal_id=id, new_internal_id=new_id)
    else:
        query = "MATCH (n:Employee) WHERE id(n) = $internal_id OPTIONAL MATCH (n)-[r:WORKS_IN]->(d:Department) OPTIONAL MATCH (n)-[r2:MANAGES]->(d2:Department) DETACH DELETE n,d2"
        tx.run(query, internal_id=id)


def get_departments(tx, name=None, number_of_employees=None, manager=None, sort=None, sortType=None):
    if sort == "name":
        if (sortType == "asc"):
            query = f"MATCH (d:Department) RETURN d ORDER BY d.name"
        if (sortType == "desc"):
            query = f"MATCH (d:Department) RETURN d ORDER BY d.name DESC"
    if sort == "number_of_employees":
        if (sortType == "asc"):
            query = f"MATCH (d:Department) MATCH (m:Employee)-[r:WORKS_IN]-(d) RETURN d.name AS name, count(m) AS number_of_employees ORDER BY number_of_employees"
        if (sortType == "desc"):
            query = f"MATCH (d:Department) MATCH (m:Employee)-[r:WORKS_IN]-(d) RETURN d.name AS name, count(m) AS number_of_employees ORDER BY number_of_employees DESC"
    if sort == "manager":
        if (sortType == "asc"):
            query = f"MATCH (d:Department) MATCH (m:Employee)-[r:MANAGES]-(d) RETURN d.name AS name, m.name AS manager ORDER BY manager"
        if (sortType == "desc"):
            query = f"MATCH (d:Department) MATCH (m:Employee)-[r:MANAGES]-(d) RETURN d.name AS name, m.name AS manager ORDER BY manager DESC"
    if not sort:
        if name:
            query = f"MATCH (d:Department {{name: '{name}'}}) RETURN d"
            result = tx.run(query).data()
            departments = [{'name': result['d']['name']} for result in result]
            return departments
        elif number_of_employees:
            query = f"MATCH (d:Department) MATCH (m:Employee)-[r:WORKS_IN]-(d) RETURN d.name AS name, count(m) AS number_of_employees ORDER BY number_of_employees {number_of_employees}"
            result = tx.run(query).data()
            departments = [{'name': result['name'], 'number_of_employees': result['number_of_employees']}
                           for result in result]
            return departments
        elif manager:
            query = f"MATCH (d:Department) MATCH (m:Employee)-[r:MANAGES]-(d) RETURN d.name AS name, m.name AS manager"
            result = tx.run(query).data()
            departments = [{'name': result['name'], 'manager': result['manager']}
                           for result in result]
            return departments
        else:
            result = tx.run("MATCH (d:Department) RETURN d").data()
            departments = [{'name': result['d']['name']} for result in result]
            return departments


def get_department_of_employee(tx, id):
    query = f"""MATCH (n:Employee) WHERE id(n) = $internal_id MATCH (n)-[:WORKS_IN]->(d:Department), 
               (m1:Employee)-[r1:MANAGES]-(d1:Department {{name:d.name}}),
               (m2:Employee)-[r2:WORKS_IN]-(d2:Department {{name:d.name}}) 
               RETURN d.name AS name, m1.name AS Manager, count(m2) AS Number_of_Employees"""
    result = tx.run(query, internal_id=id).data()
    department = [{'name': result['name'], 'manager': result['Manager'],
                   'number_of_employees': result['Number_of_Employees']} for result in result]
    return department


@ app.route('/employees', methods=['GET'])
def api_get_employees():
    params = request.args
    query = params.get('query', '')
    querytype = params.get('querytype', '')
    sort = params.get('sort', '')
    sortType = params.get('sortType', '')
    with driver.session() as session:
        employees = session.execute_read(
            get_employees, query, querytype, sort, sortType)
    res = {"employees": employees}
    return jsonify(employees)


@app.route('/employees', methods=['POST'])
def add_employee_route():
    name = request.form.get('name')
    surname = request.form.get('surname')
    department = request.form.get('department')
    position = request.form.get('position')

    if not name or not surname or not department or not position:
        response = {'message': 'Missing data'}
        return jsonify(response)

    with driver.session() as session:
        result = session.write_transaction(
            add_employee, name, surname, position, department)
        if result:
            response = {'message': 'Employee added'}
        else:
            response = {'message': 'Employee already exists'}
    return jsonify(response)


@app.route('/employees/<int:id>', methods=['DELETE'])
def delete_employee_route(id):
    if not request.json:
        with driver.session() as session:
            session.write_transaction(delete_employee, id)
        response = {'message': 'Employee deleted'}
        return jsonify(response)
    else:
        new_id = request.json.get('new_id')
        with driver.session() as session:
            session.write_transaction(delete_employee, id, new_id)
        response = {'message': 'Employee deleted'}
        return jsonify(response)


@app.route('/employees/<int:id>', methods=['PUT'])
def update_employee_route(id):

    name = request.json.get('name')
    surname = request.json.get('surname')
    position = request.json.get('position')
    department = request.json.get('department')

    with driver.session() as session:
        session.write_transaction(
            update_employee, id, name, surname, position, department)
    response = {'message': 'Employee updated'}
    return jsonify(response)


@app.route('/employees/<int:id>/subordinates', methods=['GET'])
def api_get_subordinates(id):
    with driver.session() as session:
        subordinates = session.run(
            "MATCH (e:Employee)-[:MANAGES]->(d:Department)<-[:WORKS_IN]-(s:Employee) WHERE id(e) = $id RETURN s", id=id).data()
    subordinates = [{'name': subordinate['s']['name'],
                     'surname': subordinate['s']['surname'], 'position': subordinate['s']['position']} for subordinate in subordinates]
    res = {"subordinates": subordinates}
    return jsonify(res)


@app.route('/employees/<int:id>/department', methods=['GET'])
def api_get_department_of_employee(id):
    with driver.session() as session:
        department = session.execute_read(get_department_of_employee, id)
    res = {"department": department}
    return jsonify(res)


@app.route('/departments', methods=['GET'])
def api_get_departments():
    params = request.args
    name = params.get('name', '')
    number_of_employees = params.get('number_of_employees', '')
    manager = params.get('manager', '')
    with driver.session() as session:
        departments = session.execute_read(
            get_departments, name, number_of_employees, manager)
    res = {"departments": departments}
    return jsonify(res)


@app.route('/departments/<int:id>/employees', methods=['GET'])
def api_get_employees_of_department(id):
    with driver.session() as session:
        employees = session.run(
            "MATCH (e:Employee)-[:WORKS_IN]->(d:Department) WHERE id(d) = $id RETURN e", id=id).data()
    employees = [{'name': employee['e']['name'],
                  'surname': employee['e']['surname'], 'position': employee['e']['position']} for employee in employees]
    res = {"employees": employees}
    return jsonify(res)


if __name__ == '__main__':
    app.run()