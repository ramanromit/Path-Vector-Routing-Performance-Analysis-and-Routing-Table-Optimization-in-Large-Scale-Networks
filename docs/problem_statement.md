# Path Vector Routing Performance Analysis and Routing Table Optimization in Large-Scale Networks

## 1. Project Title

**Path Vector Routing Performance Analysis and Routing Table Optimization in Large-Scale Networks**

Subject area: Computer Networks

---

## 2. Background

### 2.1 The Internet as a Collection of Networks
The Internet is made up of thousands of independent networks called **Autonomous Systems (ASes)**. An ISP, a large company like Google, and a university network can each be an AS. For data to travel from a host in one AS to a host in another, the ASes must tell each other how to reach the address ranges (prefixes) they own or can forward traffic to.

### 2.2 The Routing Protocol Between Networks
The protocol used to exchange this reachability information between ASes is the **Border Gateway Protocol (BGP)**. BGP is a **path vector** routing protocol.

### 2.3 What "Path Vector" Means
Routing protocols can be grouped by what information routers share:

| Type | Example | What a router shares / knows |
|---|---|---|
| Distance vector | RIP | "I can reach X in 3 hops." Only the distance is known. |
| Link state | OSPF | Every router knows the whole network map and computes best routes itself. |
| Path vector | BGP | "I can reach X by going through networks A → B → C." The actual list of networks on the path is shared. |

Because a path vector protocol carries the full list of networks on the path, it has two important properties:

1. **Loop prevention:** if a router sees its own network already listed in a path, it discards that route.
2. **Policy control:** networks can choose routes based on business rules such as cost, trust and partnerships, not only on the shortest distance.

---

## 3. Problem Description

As the number of networks and routers grows, path vector routing faces scalability challenges. The project addresses two linked problems.

### 3.1 Problem A: Performance of Path Vector Routing at Scale
It is not clearly understood how path vector routing behaves as a network grows from small to very large, and how it reacts when the network changes (for example, a link failing or a new node joining). The following aspects of performance need to be analyzed:

- **Convergence time:** how long it takes for all routers to agree on routes after a change in the network.
- **Message overhead:** how many routing update messages are generated when a change such as a link failure occurs.
- **Resource usage:** how much memory and CPU each router consumes.
- **Path length:** how the number of hops on chosen paths changes as the network gets larger.

### 3.2 Problem B: Routing Table Size
On the real Internet, BGP routing tables hold nearly **one million entries**. Large routing tables cause:

- Slow route lookups
- High memory consumption in routers
- Slower convergence
- More routing update traffic to process

The problem is to **reduce the size and cost of the routing table in large-scale networks without breaking reachability**, meaning every destination that was reachable before must remain reachable.

---

## 4. Objectives

1. Study how path vector routing performs in networks of increasing size, using the metrics listed in Section 3.1.
2. Identify how routing table size grows with network size and how it affects the performance metrics.
3. Reduce routing table size while preserving reachability (Section 3.2).
4. Compare the network's behaviour **before and after optimization** to show whether table size, message overhead and convergence time have improved, and by how much.

---

## 5. Scope of the Problem

- **Network scale:** small networks growing up to large ones, from tens of nodes to potentially thousands of nodes (routers or ASes).
- **Network topology:** many interconnected nodes, which may be artificially generated or based on real-world Internet topology data.
- **Events to be considered:** network growth, link failures and addition of new nodes.
- **Protocol under study:** path vector routing, as used by BGP, including loop prevention through path inspection and route selection among candidate paths.

---

## 6. Evaluation Criteria (How the Problem Is Measured)

| Metric | What it tells us |
|---|---|
| Routing table size (number of entries) | Memory and lookup cost |
| Convergence time after a change | Speed of recovery and stability |
| Number of update messages | Control traffic and processing load |
| Memory and CPU usage per router | Resource cost |
| Average path length (hops) | Quality of chosen routes |
| Reachability | Confirms no destination is lost |

---

## 7. Expected Outcome of the Project (Form of the Result)

The project is expected to produce a working program or experiment together with a written report. The report should state findings in the form of measured comparisons, for example:

> "In a network of 1000 nodes, basic path vector routing produced tables of N entries and needed X seconds to converge after a link failure. After optimization, tables were smaller by Y% and convergence improved by Z%."

The report should support these findings with graphs and tables of the measured metrics.

---

## 8. Summary

Path vector routing (as used in BGP) keeps the Internet's independent networks connected, but at large scale it suffers from huge routing tables, heavy update traffic and slow convergence. The problem is to **measure how path vector routing performs as networks grow**, and to **reduce routing table size and its associated costs while keeping every destination reachable**, then show the difference through measured results.
