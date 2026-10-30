# Étude Mécanique et Vibratoire du Bout de Fibre Optique (Micro-Cavité)

Ce document récapitule la modélisation analytique du comportement vibratoire d'un brin de fibre optique en surplomb (*cantilever*) fixé sur un tube piézoélectrique.

---

## 1. Démonstration Mathématique : Origine de $\beta_1 L \approx 1{,}875$

### 1.1 Équation du mouvement (Poutre d'Euler-Bernoulli)

Pour une poutre uniforme de section transversale $A$, de moment d'inertie de surface $I$, de module d'Young $E$ et de masse volumique $\rho$, le déplacement transversal $y(x,t)$ vérifie l'équation aux dérivées partielles :

$$E I \frac{\partial^4 y(x,t)}{\partial x^4} + \rho A \frac{\partial^2 y(x,t)}{\partial t^2} = 0$$

Par séparation des variables $y(x,t) = Y(x) \cos(\omega t)$, on obtient l'équation différentielle ordinaire spatiale :

$$\frac{\mathrm{d}^4 Y(x)}{\mathrm{d}x^4} - \beta^4 Y(x) = 0 \quad \text{avec} \quad \beta^4 = \frac{\rho A \omega^2}{E I}$$

La solution générale de cette équation différentielle est :

$$Y(x) = C_1 \cos(\beta x) + C_2 \sin(\beta x) + C_3 \cosh(\beta x) + C_4 \sinh(\beta x)$$

---

### 1.2 Conditions aux limites pour une poutre Encastrée-Libre

1. **Encastrement en $x = 0$** (déplacement et pente nuls) :
   $$Y(0) = 0 \implies C_1 + C_3 = 0 \implies C_3 = -C_1$$
   $$\left.\frac{\mathrm{d}Y}{\mathrm{d}x}\right|_{x=0} = 0 \implies \beta (C_2 + C_4) = 0 \implies C_4 = -C_2$$

   La fonction de mode s'écrit alors :
   $$Y(x) = C_1 \left( \cosh(\beta x) - \cos(\beta x) \right) + C_2 \left( \sinh(\beta x) - \sin(\beta x) \right)$$

2. **Extrémité libre en $x = L$** (moment fléchissant et effort tranchant nuls) :
   $$\left.\frac{\mathrm{d}^2 Y}{\mathrm{d}x^2}\right|_{x=L} = 0 \implies C_1 \left( \cosh(\beta L) + \cos(\beta L) \right) + C_2 \left( \sinh(\beta L) + \sin(\beta L) \right) = 0$$
   $$\left.\frac{\mathrm{d}^3 Y}{\mathrm{d}x^3}\right|_{x=L} = 0 \implies C_1 \left( \sinh(\beta L) - \sin(\beta L) \right) + C_2 \left( \cosh(\beta L) + \cos(\beta L) \right) = 0$$

---

### 1.3 Équation caractéristique

Pour qu'il existe une solution non triviale $(C_1, C_2 \neq 0)$, le déterminant du système linéaire formé par les deux équations ci-dessus doit être nul :

$$\left( \cosh(\beta L) + \cos(\beta L) \right)^2 - \left( \sinh(\beta L) - \sin(\beta L) \right) \left( \sinh(\beta L) + \sin(\beta L) \right) = 0$$

En développant :

$$\left(\cosh^2(\beta L) + 2\cosh(\beta L)\cos(\beta L) + \cos^2(\beta L)\right) - \left(\sinh^2(\beta L) - \sin^2(\beta L)\right) = 0$$

En utilisant les identités hyperboliques et trigonométriques $\cosh^2(z) - \sinh^2(z) = 1$ et $\cos^2(z) + \sin^2(z) = 1$ :

$$1 + 1 + 2\cosh(\beta L)\cos(\beta L) = 0$$

On obtient l'**équation transcendantale fondamentale** :

$$\cos(\beta L) \cdot \cosh(\beta L) = -1$$

---

### 1.4 Résolution numérique du mode fondamental

Soit $z = \beta L$. On cherche les racines de $\cos(z) \cosh(z) + 1 = 0$ :

* Pour $z \to 0$, $\cos(z)\cosh(z) \to 1 \neq -1$.
* La première racine positive $z_1 = \beta_1 L$ se situe dans l'intervalle $] \pi/2, \pi [$ :

$$\beta_1 L \approx 1{,}875104$$

*(Les modes supérieurs correspondent à $\beta_2 L \approx 4{,}694$, $\beta_3 L \approx 7{,}855$, etc.)*

---

## 2. Analyse de l'hypothèse d'élancement ($L \gg d$)

### 2.1 Remarque sur le rapport d'aspect $L/d$

Pour une longueur $L = 250\,\mu\text{m}$ et un diamètre $d = 125\,\mu\text{m}$, le rapport d'élancement vaut :

$$\frac{L}{d} = \frac{250}{125} = 2$$

Cette observation est importante :
* La théorie d'Euler-Bernoulli suppose généralement un grand élancement ($\frac{L}{d} \ge 10$) pour négliger le cisaillement transversal et l'inertie de rotation des sections.
* Lorsque $\frac{L}{d} \sim 2$, la poutre est "courte" ou "trapue". La théorie appropriée est celle de **Timoshenko**.

### 2.2 Impact de la théorie de Timoshenko

La déformation par cisaillement rend la structure légèrement plus souple. La fréquence propre réelle $f_{\text{Timoshenko}}$ est abaissée par rapport à l'estimation d'Euler-Bernoulli $f_{\text{EB}}$ :

$$f_{\text{Timoshenko}} \approx \frac{f_{\text{EB}}}{\sqrt{1 + \alpha \left(\frac{d}{L}\right)^2}}$$

Pour $\frac{L}{d} = 2$, la correction abaisse la fréquence fondamentale d'environ $20\%$ à $30\%$ :
* **Euler-Bernoulli :** $f_0 \approx 1{,}6\text{ MHz}$
* **Timoshenko (corrigé) :** $f_0 \approx 1{,}1 \text{ à } 1{,}3\text{ MHz}$

**Conclusion pratique :** Bien que la valeur exacte de la fréquence décroisse légèrement, l'ordre de grandeur reste fermement ancré dans le **Mégahertz ($> 1\text{ MHz}$)**. Les conclusions physiques quant à l'insensibilité aux bruits acoustiques et mécaniques ($< 10\text{ kHz}$) restent inchangées.

---

## 3. Synthèse des Équations Littérales et Valeurs Numériques

### 3.1 Grandeurs géométriques et matérielles

* Section de la fibre : $A = \frac{\pi d^2}{4}$
* Moment d'inertie de surface : $I = \frac{\pi d^4}{64}$
* Module d'Young de la silice : $E \approx 72\text{ GPa}$
* Masse volumique : $\rho \approx 2200\text{ kg/m}^3$
* Vitesse du son dans la silice : $v = \sqrt{\frac{E}{\rho}} \approx 5720\text{ m/s}$

---

### 3.2 Fréquence propre fondamentale ($f_0$)

#### Expression littérale :

$$f_0 = \frac{\omega_0}{2\pi} = \frac{(\beta_1 L)^2}{2\pi L^2} \sqrt{\frac{E I}{\rho A}} = \frac{(1{,}875)^2}{8 \pi} \cdot \frac{d}{L^2} \sqrt{\frac{E}{\rho}}$$

En simplifiant la constante $\frac{(1{,}875)^2}{8 \pi} \approx 0{,}1401$ :

$$f_0 \approx 0{,}14 \cdot \frac{d}{L^2} \sqrt{\frac{E}{\rho}}$$

---

### 3.3 Raideur équivalente et Amplitude des vibrations thermiques ($\sigma_y$)

#### Raideur équivalente à l'extrémité ($k_{\text{eff}}$) :

$$k_{\text{eff}} = \frac{3 E I}{L^3} = \frac{3 \pi E d^4}{64 L^3}$$

#### Amplitude quadratique moyenne du bruit thermique ($\sigma_y = \sqrt{\langle y^2 \rangle}$) :

En appliquant le théorème d'équipartition de l'énergie ($\frac{1}{2} k_{\text{eff}} \langle y^2 \rangle = \frac{1}{2} k_B T$) :

$$\sigma_y = \sqrt{\frac{k_B T}{k_{\text{eff}}}} = \sqrt{\frac{64 k_B T L^3}{3 \pi E d^4}}$$

---

### 3.4 Table des valeurs numériques ($T = 300\text{ K}$, $L = 250\,\mu\text{m}$, $d = 125\,\mu\text{m}$)

| Grandeur | Formule littérale | Valeur numérique |
| :--- | :--- | :--- |
| **Fréquence propre ($f_0$)** | $0{,}14 \cdot \frac{d}{L^2} \sqrt{\frac{E}{\rho}}$ | $\approx 1{,}6\text{ MHz}$ |
| **Raideur de l'extrémité ($k_{\text{eff}}$)** | $\frac{3 \pi E d^4}{64 L^3}$ | $\approx 1{,}66 \times 10^5\text{ N/m}$ |
| **Bruit thermique ($\sigma_y$)** | $\sqrt{\frac{64 k_B T L^3}{3 \pi E d^4}}$ | $\approx 0{,}16\text{ pm}$ ($1{,}6 \times 10^{-13}\text{ m}$) |
```