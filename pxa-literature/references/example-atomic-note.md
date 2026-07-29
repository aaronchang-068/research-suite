---
type: atomic
topic: 基於空氣動力條件的結構佈局規劃
cluster: 氣動載荷
tags: []
created: 2026-07-04
status: stable
---

# 配平修正演算法（Trim Correction Algorithm）

## 核心陳述
> 配平修正演算法在流場收斂過程中，反覆調整攻角與控制面偏轉，使當前氣動係數逼近目標機動所需值。

## 文獻回顧

以 CFD 為基礎的撓性飛機機動載荷分析中，配平問題的表述與剛性配平相反：升力與力矩係數由指定機動決定，未知量為達成該係數所需的攻角 $\alpha$ 與控制面偏轉角 $\delta$。此一問題設定最早由 Raveh 與 Karpel (1999) 系統化處理。他們指出，非線性 CFD 之氣動係數對配平變數的依賴為隱式且非線性，故配平不能一次求解，而應嵌入流場迭代收斂的過程——每隔若干流場迭代即比較當前與目標係數、解修正方程更新 $\alpha$ 與 $\delta$，使配平與流場收斂同時完成，撓性機動分析的成本因而接近單次剛性 CFD。

配平導數的取得是該方法可行性的關鍵。Raveh 與 Karpel (1999) 建議以線性氣動彈性分析提供近似導數；Raveh、Karpel 與 Yaniv (2000) 在非線性設計載荷的產生流程中進一步證實：導數取自 MSC/NASTRAN 之 Doublet Lattice 模組即已足夠，且導數精度僅影響收斂速率、不影響收斂到的配平解。此一結論大幅降低了演算法的實作門檻，因為它免除了以有限差分對 CFD 求導的昂貴計算。

兩文對耦合強度的討論一致：當攻角主控升力、控制面主控力矩（弱耦合）時，修正方程的交叉導數項 $\tilde C_{M\alpha}$、$\tilde C_{L\delta}$ 可以忽略；強耦合時若忽略則收斂緩慢並出現震盪，須保留交叉項並輔以鬆弛（relaxation）避免過度修正。

## 符號表

| 符號 | 意義 |
|------|------|
| $q$, $S$, $\bar c$ | 動壓、參考面積、平均氣動弦長 |
| $[M_R]$, $[\phi_R]$ | 剛體廣義質量矩陣、剛體模態矩陣 |
| $\{\ddot\xi_R\}$ | 指定機動之剛體廣義加速度 |
| $\{F_A\}$ | CFD 表面氣動力向量 |
| $\tilde C_{L\alpha},\tilde C_{L\delta},\tilde C_{M\alpha},\tilde C_{M\delta}$ | 近似配平導數 |
| 下標 $req$ / $cur$ | 目標值／當前值 |

## 數學形式

目標係數由指定的剛體加速度決定（Raveh & Karpel 1999, Eq. 9）：

$$
qS\begin{Bmatrix}C_L\\ C_M\,\bar c\end{Bmatrix}_{req}=[M_R]\{\ddot\xi_R\}
\tag{1}
$$

當前係數由 CFD 表面氣動力投影至剛體模態（同文 Eq. 10）：

$$
qS\begin{Bmatrix}C_L\\ C_M\,\bar c\end{Bmatrix}_{cur}=[\phi_R]^T\{F_A\}
\tag{2}
$$

修正方程（同文 Eq. 12；第二列之 $\bar c$ 因子使力矩列與式 (1)、(2) 之 $C_M\bar c$ 因次一致）：

$$
\begin{Bmatrix}\Delta\alpha\\ \Delta\delta\end{Bmatrix}=
\begin{bmatrix}\tilde C_{L\alpha}&\tilde C_{L\delta}\\ \tilde C_{M\alpha}\,\bar c&\tilde C_{M\delta}\,\bar c\end{bmatrix}^{-1}
\begin{Bmatrix}C_L\\ C_M\,\bar c\end{Bmatrix}_{req-cur}
\tag{3}
$$

## 演算法程序

1. 指定機動 $\{\ddot\xi_R\}$，以式 (1) 計算目標係數；初始化 $\alpha$、$\delta$。
2. 推進 CFD 流場迭代若干步，以式 (2) 計算當前係數。
3. 以式 (3) 解修正量 $\Delta\alpha$、$\Delta\delta$（必要時乘以鬆弛因子）。
4. 施加修正：$\Delta\alpha$ 改變遠場邊界條件；$\Delta\delta$ 以控制面單位剛體旋轉模態重生氣動網格（根部設 blending zone 避免幾何不連續）；機動角速率以旋轉座標系附加項加入流體方程。
5. 重複步驟 2–4 直到 $\{C_L,\ C_M\bar c\}_{req-cur}$ 收斂於容許值內，配平與流場同步收斂。

## 關鍵要點
- 配平嵌入流場收斂過程逐步修正，撓性機動成本接近剛性 CFD 單次解。
- 近似（線性）導數即可收斂（Raveh et al. 2000 證實）；導數品質僅影響收斂速率。
- 弱耦合可忽略交叉導數項；強耦合須保留並以鬆弛穩定。
- 實作：攻角改遠場條件、控制面以旋轉模態重生網格、角速率以旋轉座標項引入。

## 相關概念
- [[Maneuver Load Analysis]] — 配平修正是機動載荷分析三層迭代的最外層
- [[Static Aeroelastic Trim]] — 本演算法達成的即為撓性飛機的配平平衡狀態
- [[Aileron Effectiveness]] — 控制面偏轉在配平中的效果與控制效率直接相關
- [[Doublet Lattice Method]] — 近似配平導數可取自 DLM 線性氣動彈性分析

## 來源
- [[1999 Raveh Karpel - Structural Optimization CFD Maneuver Loads]]（Maneuver Trim, Eq. 9–12, p.1009）
- [[2000 Raveh Karpel Yaniv - Nonlinear Design Loads Maneuvering Elastic Aircraft]]（Maneuver Trim, Eq. 6–8, p.315）
