https://github.com/HKUDS/OpenHarness

港大出了一个开源项目叫 OpenHarness，名字直译就是"开放智能体框架"。

看起来没什么特别的——43 个工具，54 个命令，技能系统，记忆系统，多 Agent 协调。

但它的核心代码让我很震撼。

核心引擎就三行：

```python
while True:
    response = await api.stream(messages, tools)
    if response.stop_reason != "tool_use":
        break
    for tool_call in response.tool_uses:
        result = await harness.execute_tool(tool_call)
        messages.append(tool_results)
```

一个循环。无限循环。

就这么一个简单的循环，外面套上工具、技能、记忆、权限，一个智能体就跑起来了。

这让我意识到一个问题：大多数人构建 AI Agent 的方向，从一开始就错了。

**我们在用 2025 年的思维，搭建 2026 年的智能体。**

![](http://mmbiz.qpic.cn/sz_mmbiz_png/4cnGXq110SNjE1ONlN0ibC0JQEDicEGREp1BCANyROicYxiaicEAotI9ljiboBfgfwlRCbIIwlrLACJtKOFAB41eKErUmd6A6GnXAmxhCXI7uBST4/0?wx_fmt=png)

## 从画流程图到搭舞台

大部分人是怎么做 Agent 的？

学 LangGraph，用 LangChain。画流程图：第一步做什么，第二步做什么，第三步遇到条件 A 走这里，遇到条件 B 走那里。用代码把所有可能的分支都写死。

这是流水线思维。你画好了每一步的路径，AI 只能按你的路线走。

这本质上是**不信任 AI**——你觉得它会乱来，所以你要在每一步都设关卡。

但 OpenHarness 给了我们另一种答案。

它的核心不是"流程"，而是**循环 + 约束**。

你只需要做三件事：

- 提供工具（能做什么）
- 设置约束（不能做什么）
- 定义目标（要什么）

然后让 AI 自己在这个舞台上去试、去迭代、去修正。

你搭好了舞台，演员自己知道怎么走。

**这不是一样的思路。这是两种完全不同的哲学。**

流水线的本质是"人控制 AI"。Harness 的本质是"人给 AI 画边界，AI 在里面自由发挥"。

当 Agent 的能力越来越强，用流水线的方式只会成为瓶颈。因为你写得越快，越追不上 AI 的能力增长。

**AI 需要的不是更长的操作手册，而是一个更广阔的舞台。**

## 人工定义规则是死路

我有切身体会。

搭建自己的 AI Agent 时，我发现**人工添加这些规则非常痛苦**。

写 Skill，要一个字一个字地描述这个工具怎么用、参数是什么、返回值是什么、边界在哪。写 Hook，要手动判断哪些场景需要拦截、哪些不需要。写权限，要逐条定义路径、命令、操作的规则。

每一条都是人写的。每一条都是静态的。

但业务需求在变，代码库在变，AI 的能力也在变。人工写的规则很快就会过时。

正确的做法应该是：**人定义目标，让 AI 自己去完善规则和工具**。

你告诉 AI：你的目标是让这个项目能正常运行。AI 自己发现缺了什么 Skill，自己去写。你只需要在关键节点 review 就行。

不是 AI 需要你来手把手教它怎么写规则，而是你需要让 AI 自己去迭代规则。

## 港大 OpenHarness 的设计哲学

这就是 OpenHarness 最核心的设计理念。

它不是一个框架——它是一个**循环 + 基础设施**的最小实现。

![](http://mmbiz.qpic.cn/sz_mmbiz_png/4cnGXq110SMJOhGPyFhrP0zuHKvzmpKYwp0DZibGuqbJZlwgQSmmyu0eyexNxpKCZr35fYqibXTb7BTicDsENv5Q0HbQWxLziaTHNNzAIibMV4m0/0?wx_fmt=png)

你看它的架构：

- 引擎：`while True` 循环
- 工具库：43 种（文件操作、Shell、搜索、网络、MCP）
- 技能系统：按需要加载 `.md` 文件
- 记忆系统：跨Session 持久化
- 权限系统：多级模式、路径规则、命令拦截
- Hook 系统：工具执行前后的事件钩子
- 多 Agent：子 Agent 生成、任务委派

所有东西都围着一个循环转。AI 的智力由模型提供，Agent 的能力边界由 Harness 提供。

**OpenHarness 的核心不是代码量。是它只做了一件事：让 AI 能自己迭代。**

## Harness 的真正价值

很多人觉得 Harness 就是个工具库。错了。

Harness 的真正价值不是"多给 AI 一些工具"。

**Harness 的真正价值是让 AI 在边界内自己完善自己。**

想象一家公司。

老板不会给每个员工写一份 500 页的操作手册——你告诉他目标是什么、底线是什么、需要什么资源、有什么权限。然后他自己想办法。

这就是 Harness 的设计哲学。它不是在画流程图——它在定义一个环境，让 AI 能在这个环境里自主运行、自主迭代、自主修正。

## 未来会怎样？

当 Harness 足够完善，Agent 能自己完善自己，会发生什么？

**第一，开发从"写代码"变成"定义目标"。**

你不再需要编写每一个函数、每一个接口、每一个路由。你只需要告诉 AI：我要什么功能，有什么约束条件，用什么技术栈。AI 自己迭代，自己做。

**第二，Agent 的复杂度上限被移除了。**

以前你做 Agent，复杂度受到你编写流程图的能力限制。你画不出的复杂流程，Agent 就不会。现在 AI 自己能处理复杂流程——你不需要画，它自己迭代。

**第三，智能体的真正自主性。**

当 AI 不仅能执行任务，还能定义规则、修改工具、更新技能——它就不再是一个工具了。它是一个能自我进化的智能体。

## 你现在应该做什么？

不要学 LangGraph。不要画流程图。不要试图把所有分支都写死。

**先搭舞台。**

- 给 AI 工具（它能做什么）
- 给 AI 约束（它不能做什么）
- 给 AI 目标（它要什么）
- 然后放手

让 AI 自己去迭代、去完善、去发现你都没想到的问题。

**AI 最强大的能力，不是执行你给它的步骤。**

**而是你给了一个舞台，它自己能走出你没想到的路。**