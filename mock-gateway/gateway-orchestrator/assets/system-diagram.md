```plantuml
card "docker swarm" as swarm1 {
    frame "redis service" {
        database redis as redis
    }
    frame "submitter service" {
        component submitter as submitter
    }
    frame "orchestrator service" #lightblue {
        component orchestrator as orch
    }
    frame "weightstack controller service" {
        component "weightstack controller" as ws1
        component "weightstack controller" as ws2
        ws1 -[hidden]- ws2
    }
    frame "treadmill controller service" {
        component "treadmill controller" as tm1
        component "treadmill controller" as tm2
    }
    frame "bike controller service" {
        component "bike controller" as bk1
    }
}


cloud "backend" {
    database "machines"
}

component "docker.sock" as dockersocket

redis <-- orch
redis <-- submitter

submitter <-- machines

orch --> dockersocket

bk1 -> redis

tm1 --> redis
tm2 --> redis

redis <- ws2
redis <- ws1

note right of dockersocket : Scales controller services in docker swarm

```