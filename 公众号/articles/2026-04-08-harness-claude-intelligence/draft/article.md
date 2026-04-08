Anthropic 最近发了一篇博客，讲怎么构建跟得上 Claude 能力进化的应用。https://claude.com/blog/harnessing-claudes-intelligence

这篇文章的核心观点很简单：**你给 Claude 写的管控代码，正在成为它的瓶颈。**

Agent harness（智能体框架）本质上是一堆假设——假设 Claude 不会自己安排工具调用顺序，假设它不会管理自己的上下文，假设它记不住重要信息。但随着模型越来越强，这些假设正在一个一个过期。

Anthropic 给出了三个构建模式。

## 一、用 Claude 已经会的东西

2024 年底，Claude 3.5 Sonnet 在 SWE-bench Verified 上拿到 49% 的成绩——当时的 SOTA。它用的工具只有两个：bash 和文本编辑器。

不是因为没有更好的工具，而是这两个工具 Claude **真正理解**。它知道怎么用 bash 管道把多个命令串起来，知道怎么用文本编辑器精确修改文件。随着模型升级，它对这两个工具的使用越来越熟练。

Anthropic 的经验是：Claude 会把简单工具**组合**成复杂能力。Agent Skills、程序化工具调用、记忆工具——这些听起来高大上的功能，底层全是 bash 和文本编辑器的组合。

这跟很多人的直觉相反。大部分开发者倾向于给 AI 封装高层抽象——专门的搜索工具、专门的代码分析工具、专门的数据库查询工具。但 Anthropic 的实践证明，给 Claude 通用工具 + 让它自己组合，比给它一堆专用工具效果更好。

**因为通用工具的能力会随模型升级自动增长，而专用工具不会。**

## 二、问自己：我可以不做什么了？

这是整篇文章最有价值的部分。Anthropic 提出了一个反直觉的开发准则：每次 Claude 升级后，不是想"我能加什么新功能"，而是想"**我可以删掉哪些代码了**"。

### 让 Claude 自己编排行动

传统做法是：Claude 调用工具 → 结果回到上下文窗口 → Claude 看完后决定下一步。每一步的中间结果都要过一遍 Claude 的"大脑"。

问题是：很多时候 Claude 根本不需要看中间结果。比如读一张大表只为了分析其中一列，整张表的 token 成本都浪费了。

Anthropic 的方案是给 Claude 一个代码执行工具（bash 或 REPL）。Claude 可以写代码来表达"先调用 A 工具，过滤结果，再传给 B 工具"——中间数据不经过上下文窗口，只有最终输出回到 Claude。

编排决策从框架转移到了模型。而且因为代码是通用的编排方式，一个强大的编程模型同时也是一个强大的通用 Agent。

在 BrowseComp（网页浏览基准测试）上，让 Opus 4.6 自己过滤工具输出，准确率从 45.3% 跳到了 61.6%。

![](http://mmbiz.qpic.cn/mmbiz_png/4cnGXq110SMeibRFaeG0DZQwUNK8D3ELL1OUB3b0hLBWo8SjNb0BLkk2hVGjZSBcnxK3ZH2JuLfGRoUgxcVD5Q6OPBUtbRuiauj251qcXlnto/0?wx_fmt=png)

### 让 Claude 管理自己的上下文

传统做法是手写大量 system prompt，把所有任务指令都预加载进上下文。问题是：指令越多，Claude 的注意力越分散，而且大部分指令在当前任务中用不到。

Skills 系统解决了这个问题。每个 Skill 的 YAML 头信息（简短描述）预加载到上下文，完整内容只在需要时才被 Claude 主动读取。这是**渐进式披露**——Claude 自己决定什么时候需要什么信息。

Context editing 是反方向的操作：让 Claude 删除过时或无关的上下文，比如旧的工具输出或思考过程。

Subagent（子代理）则让 Claude 知道什么时候该 fork 出一个新的上下文窗口来隔离特定任务。Opus 4.6 使用子代理后，BrowseComp 成绩比最佳单 Agent 运行又提升了 2.8%。

### 让 Claude 持久化自己的上下文

长时间运行的 Agent 会超出单个上下文窗口的限制。传统做法是在模型外部搭建检索系统来管理记忆。

Anthropic 的做法是让 Claude **自己选择**记什么。

Compaction（压缩）让 Claude 总结过去的上下文来维持长期任务的连续性。不同模型的表现差异很大：Sonnet 4.5 不管给多少压缩预算，在 BrowseComp 上都卡在 43%。Opus 4.5 能到 68%，Opus 4.6 到了 84%。

Memory folder（记忆文件夹）是另一种方式。Claude 把重要信息写入文件，需要时再读取。给 Sonnet 4.5 一个记忆文件夹，BrowseComp-Plus 准确率从 60.4% 提升到 67.2%。

文章举了一个很有意思的例子：让不同版本的 Claude 玩宝可梦。

Sonnet 3.5 把记忆当成流水账，记录 NPC 说了什么，14000 步之后积累了 31 个文件（包括两个几乎重复的关于毛虫宝可梦的笔记），还卡在第二个城镇。

Opus 4.6 在同样步数下只有 10 个文件，按目录组织，已经拿了三个徽章，并且写了一个从自己失败中提炼出来的经验文件：

> B1F y=16 wall CONFIRMED SOLID at ALL x=9-28 (step 14557)

这不是信息记录。这是战术笔记。

![](http://mmbiz.qpic.cn/mmbiz_png/4cnGXq110SNjHVXUoQza6p0nIVptxahDjE86bCoab6Jq9RLIPRia6UfotzWdmNmWSw9tNXmllzib6Zs5WrP1xlvibPsqTiadUST3U3CcADcHz6A/0?wx_fmt=png)

## 三、谨慎设定边界

虽然要"少管"，但该管的地方不能松。Anthropic 指出了几个框架必须承担的职责。

### 缓存优化

Claude API 是无状态的。每一轮对话，框架都要把历史消息、工具描述、指令全部打包发过去。缓存能把这部分成本降到原来的十分之一。

几个关键原则：

- **静态在前，动态在后**：system prompt 和工具定义放前面（容易命中缓存）
- **不要换模型**：缓存是模型专属的，换模型会失效
- **不要随意增删工具**：工具在缓存前缀里，改了就失效
- **用消息追加更新**：不要直接改 prompt，用 system-reminder 消息追加

### 声明式工具用于安全和 UX

bash 工具给了 Claude 巨大的灵活性，但对框架来说，每个 bash 命令看起来都一样——一个字符串。框架没法区分"读文件"和"删除文件"。

把高风险操作提升为**专门的工具**，框架就能拦截、审计、确认。比如不可逆的操作（外部 API 调用）可以加用户确认，写文件工具可以加过时检查防止覆盖。

但这个边界也要不断调整。Claude Code 的 auto-mode 用另一个 Claude 来判断 bash 命令是否安全，减少了对专用工具的需求。

## 我的理解

这篇博客的核心不是在教你怎么用 Claude API。它在讲一个更根本的问题：**当 AI 能力持续进化时，应用架构应该怎么设计？**

答案是：设计成可以不断**删除代码**的架构。

Anthropic 举了一个例子。他们给长期任务构建的 Agent 中，Sonnet 4.5 会在感知到上下文快满时提前结束任务（"上下文焦虑"）。他们专门写了代码来重置上下文窗口。结果 Opus 4.5 一出来，这个行为消失了。那些补偿代码变成了死代码。

这说明了一件事：**在 Agent 开发中，你对模型做的每一个假设都有保质期。**

好的 Agent 框架不是功能越多越好。它应该是一个不断瘦身的系统——每次模型升级，都把一部分控制权还给模型。

Anthropic 在文末引用了 Rich Sutton 的 The Bitter Lesson："利用通用计算方法的研究者最终会赢。"放到 Agent 开发上就是：**别替 AI 做决定，给它工具和边界，让它自己来。**

![](http://mmbiz.qpic.cn/mmbiz_png/4cnGXq110SOcWkIOjibH7JoxSXIQ4e0NXmbafKLYTKmpNaxic4zh5auysy3RjE1pqFLABCayp78KXb6DmrVmy0s2FpkdXREC4hk12BknUWU7s/0?wx_fmt=png)
