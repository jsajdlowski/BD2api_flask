CREATE (Stachu:Employee {name:"Stachu", surname: "Wokulski", position:"CEO"})
CREATE (Mike:Employee {name:"mike", surname: "Tyson", position:"Janitor"})
CREATE (Borys:Employee {name:"Borys", surname: "Grzegorz", position:"BodyGuard"})
CREATE (Ania:Employee {name:"Ania", surname: "Robak", position:"Secretary"})
CREATE (Janusz:Employee {name:"Janusz", surname: "Walczuk", position:"Programmer"})
CREATE (HR:Department {name:"HR"})
CREATE (IT:Department {name:"IT"})

MATCH
  (a:Employee),
  (b:Department)
WHERE a.name = 'Stachu' AND b.name = 'IT'
CREATE (a)-[r:WORKS_IN]->(b)
RETURN type(r)

MATCH
  (e:Employee),
  (d:Department)
WHERE e.name = 'mike' AND d.name = 'IT'
CREATE (e)-[r:WORKS_IN]->(d)<-[:MANAGES]-(e)
RETURN type(r)

MATCH
  (e:Employee),
  (d:Department)
WHERE e.name = 'Borys' AND d.name = 'HR'
CREATE (e)-[r:WORKS_IN]->(d)
RETURN type(r)

MATCH
  (e:Employee),
  (d:Department)
WHERE e.name = 'Ania' AND d.name = 'HR'
CREATE (e)-[r:WORKS_IN]->(d)
RETURN type(r)

MATCH
  (e:Employee),
  (d:Department)
WHERE e.name = 'Janusz' AND d.name = 'IT'
CREATE (e)-[r:WORKS_IN]->(d)
RETURN type(r)