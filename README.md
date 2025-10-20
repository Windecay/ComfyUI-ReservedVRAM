A simple node that can dynamically adjust the reserved memory of a workflow in real-time, used to avoid the utilization of shared memory.

更新
2025-10-21增强节点功能

1，可以作为随机种子节点，每次运行均检测和和修改显存策略。可选开关。

2，前置输入可以不接。增加后置输出随机种子和预留数值。后置输出也可以不接。

3，增加前置清理显存的开关，可以作为显存清理节点使用。可以选择在输出前用手动模式恢复环境变量为默认（0.6GB）。

4，增加最大预留值，在Auto档生效，某些情况防止预留过大，但也会削弱Auto的能力。

new
2025-10-21 Enhanced Node Features
1. Can function as a random seed node, detecting and modifying VRAM strategy with each run. Optional toggle.
2. Front-end input can be left unconnected. Added back-end output for random seed and reserved value. Back-end output can also be left unconnected.
3. Added a front-end VRAM cleanup toggle, allowing use as a VRAM cleanup node. Option to restore environment variables to default (0.6GB) manually before output.
4. Added maximum reserved value, effective in Auto mode, preventing excessive reservation in certain cases while slightly reducing Auto mode's capability.
<img width="1919" height="1461" alt="image" src="https://github.com/user-attachments/assets/5b3af05d-5051-4fc9-b2e7-fd7cb7cfe719" />

2025-10-10新增自动模式，自动模式会检测系统“已使用”的显存数量，再叠加用户设置值进行预留。避免多进程用户因为显存问题卡住运行。

预留数值可以为负值，配合自动模式计算用。
—————————————————————————————————————————

一个可以实时调节工作流预留显存的简单节点，可以用于规避共享显存的使用，跑满显卡最大功率，解除显存焦虑。

接在排行较前的节点处即可，观察windows任务管理器共享显存溢出多少，就需要设置保留多少（可以略微多一点），填入该数值。运行工作流实时生效，输入单位是GB。

![N57)EGC5978{(Y36IV~13AL](https://github.com/user-attachments/assets/245e5f11-c16d-403c-a438-567040f12ebf)

![19~HL`3H{F %%LBE)3~3GPC](https://github.com/user-attachments/assets/fd8b61e4-e2e5-42ca-a516-2ddc1c7d0d8d)

![_$)59`(5~XN5OH7NM %WHU](https://github.com/user-attachments/assets/bb652d70-805b-452e-a522-f271c8c70bf4)

![image](https://github.com/user-attachments/assets/48f8ca7f-2a13-4ef5-a5bb-5f6ef9c974e3)
