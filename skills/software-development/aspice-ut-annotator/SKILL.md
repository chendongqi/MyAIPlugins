---
name: aspice-ut-annotator
description: >
  为汽车ASPICE SWE.4流程生成符合规范的单元测试注释。针对Java/Kotlin单元测试文件（JUnit/Mockito/MockK等），
  自动分析测试方法与被测方法的对应关系，生成包含ComponentName、Owner、TestCaseID、UnitName、
  DesignMethods、InputData、ExpectedOutput等字段的结构化注释块。

  触发场景：
  (1) 用户要求为单元测试文件生成ASPICE规范注释
  (2) 用户提供测试文件或目录路径，要求批量生成测试注释
  (3) 用户提到SWE4、单元测试注释、测试用例注释、ASPICE测试文档化
  (4) 用户要求更新或覆盖已有的单元测试注释

  触发关键词：单元测试注释、测试用例注释、SWE4、ASPICE注释、UT注释、test annotation、
  generate test comments、测试注释生成、ut-annotate
---

# ASPICE 单元测试注释生成器

为Java/Kotlin单元测试文件生成符合ASPICE SWE.4规范的结构化注释。

## 注释格式

```java
/**
 * ComponentName : "DiagClient".
 * Owner : "shengwang.zhang".
 * TestCaseID : "SWE4-ClassName::methodName-001".
 * UnitName : "ClassName::methodName(ParamType1 param1, ParamType2 param2)".
 * DesignMethods : ["require","error"].
 * InputData : ["Prequisite: ...; Input: ..."].
 * ExpectedOutput : ["..."].
 */
```

**格式严格要求：**
- 每个字段独占一行，以 ` * ` 开头
- 字段名后接 ` : `（空格冒号空格）
- 字符串值用双引号包裹，末尾加 `.`
- 数组值用 `["item1","item2"]` 格式，末尾加 `.`
- 注释块紧贴在测试方法的 `@Test` 注解（Java）或 `@Test` / `fun test...`（Kotlin）之前
- 如果 `@Test` 注解前还有其他注解（如 `@DisplayName`），注释块放在所有注解之前

## 工作流程

### Phase 1: 收集必要参数

开始前必须确认以下参数，缺失时向用户询问：

| 参数 | 说明 | 示例 |
|------|------|------|
| `targetPath` | 测试文件或目录路径 | `src/test/java/com/example/` |
| `ComponentName` | 组件名称 | `"DiagClient"` |
| `Owner` | 负责人 | `"shengwang.zhang"` |

### Phase 2: 发现测试文件

1. 如果 `targetPath` 是单个文件，直接使用
2. 如果是目录，用 Glob 扫描：
   - Java: `**/*Test.java`, `**/*Tests.java`, `**/*TestCase.java`
   - Kotlin: `**/*Test.kt`, `**/*Tests.kt`
3. 列出发现的文件，向用户确认处理范围

### Phase 3: 逐文件处理

对每个测试文件执行以下步骤：

#### 3.1 读取测试文件，解析所有测试方法

识别测试方法的标志：
- Java: `@Test` 注解修饰的方法
- Kotlin: `@Test` 注解修饰的函数

对每个测试方法提取：
- 方法名（如 `testSaveVersion_success`）
- 方法体内容（用于后续分析）

#### 3.2 定位被测类和源文件

从测试文件推断被测类：
- 测试类名 `FooServiceTest` → 被测类 `FooService`
- 测试类名 `FooServiceTests` → 被测类 `FooService`
- 查看import语句和类中的成员变量确认被测类
- 用 Glob 在项目的 `src/main/` 或同级源码目录中找到被测类源文件

#### 3.3 定位被测方法

从测试方法中推断被测方法：
- 分析测试方法体中的方法调用，找到对被测对象调用的方法
- 在被测类源文件中找到该方法的完整签名（含参数类型和参数名）
- 如果无法确定，标记为 `"Unknown"` 并在完成后提醒用户

#### 3.4 构造各字段

**TestCaseID**: `SWE4-{被测类名}::{被测方法名}-{序号}`
- 序号三位数字，同一个被测方法的多个测试用例按出现顺序编号：001, 002, 003...
- 维护一个计数器 map，key 为 `ClassName::methodName`

**UnitName**: `{被测类名}::{被测方法名}({参数类型 参数名, ...})`
- 从被测类源文件中读取方法的完整签名
- 保留参数类型和参数名，如 `"DiagClient::saveVersion(int version, String tag)"`

**DesignMethods**: 从测试代码分析判断，可多选：
- `"require"` — 测试正常业务逻辑/需求功能
- `"error"` — 测试异常、错误路径（assertThrows, expectedException, catch块）
- `"bound"` — 测试边界值（0, -1, MAX_VALUE, 空字符串, null, 空集合等）
- `"equivalence"` — 测试等价类划分（参数化测试, 多组典型输入覆盖不同分区）

**InputData**: `["Prequisite: {前置条件}; Input: {输入参数}"]`
- 前置条件：mock设置、对象创建、环境准备等（从 `@Before`/`@BeforeEach`/`setUp` 和测试方法前半部分提取）
- 输入参数：被测方法的实际入参值

**ExpectedOutput**: `["期望输出的描述"]`
- 从 assert 语句、verify 语句、expected异常中提取
- 简洁描述期望结果，如 `"return true"`, `"throw IllegalArgumentException"`, `"verify service.save() called once"`

#### 3.5 插入/替换注释

- 在测试方法的第一个注解（如 `@Test`、`@DisplayName` 等）之前插入注释块
- 如果该位置已有 `/** ... */` 格式的文档注释，**整块替换**
- 保持原有代码缩进风格

### Phase 4: 完成确认

1. 输出处理摘要：处理了多少文件、多少测试方法
2. 列出无法确定被测方法的测试用例（标记为 `Unknown` 的）
3. 提示用户检查和补充

## 注意事项

- 只修改注释，不改动任何测试代码逻辑
- 保持文件原有的编码格式和换行符风格
- 对参数化测试（`@ParameterizedTest`），每个参数化方法视为一个测试用例
- 对嵌套测试类（`@Nested`），类名使用外部类名
- 如遇到被测方法重载（overload），UnitName 需要精确匹配测试中调用的那个重载版本
