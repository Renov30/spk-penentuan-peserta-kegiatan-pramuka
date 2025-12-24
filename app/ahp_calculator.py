"""
Modul untuk perhitungan AHP (Analytical Hierarchy Process) lengkap
sesuai dengan teori Fuzzy AHP dari PDF.
"""
import numpy as np
from typing import List, Tuple, Dict
from decimal import Decimal, getcontext

# Set precision untuk perhitungan
getcontext().prec = 28

# Tabel RI (Random Index) untuk uji konsistensi
RI_TABLE = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
    6: 1.24, 7: 1.32, 8: 1.41, 9: 1.46, 10: 1.49,
    11: 1.51, 12: 1.58
}

# Skala Triangular Fuzzy Number (TFN) sesuai PDF
TFN_SCALE = {
    1: (1, 1, 1),
    2: (1/2, 1, 3/2),
    3: (1, 3/2, 2),
    4: (3/2, 2, 5/2),
    5: (2, 5/2, 3),
    6: (5/2, 3, 7/2),
    7: (3, 7/2, 4),
    8: (7/2, 4, 9/2),
    9: (4, 9/2, 5)
}

def get_tfn_reciprocal(tfn: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Mendapatkan kebalikan dari TFN"""
    l, m, u = tfn
    return (1/u, 1/m, 1/l)


class AHPCalculator:
    """Kelas untuk perhitungan AHP lengkap"""
    
    def __init__(self, criteria_names: List[str]):
        """
        Inisialisasi AHP Calculator
        
        Args:
            criteria_names: List nama kriteria
        """
        self.criteria_names = criteria_names
        self.n = len(criteria_names)
        self.pairwise_matrix = None
        self.eigenvector = None
        self.lambda_max = None
        self.ci = None
        self.cr = None
        self.weights = None
        
    def set_pairwise_matrix(self, matrix: np.ndarray):
        """
        Set matriks perbandingan berpasangan
        
        Args:
            matrix: Matriks n x n dengan nilai perbandingan
        """
        if matrix.shape != (self.n, self.n):
            raise ValueError(f"Matrix harus berukuran {self.n}x{self.n}")
        self.pairwise_matrix = matrix
        
    def calculate_eigenvector(self) -> np.ndarray:
        """
        Menghitung eigenvector dari matriks perbandingan berpasangan
        menggunakan metode geometric mean
        
        Returns:
            Eigenvector yang sudah dinormalisasi
        """
        if self.pairwise_matrix is None:
            raise ValueError("Matriks perbandingan belum di-set")
        
        # Hitung geometric mean untuk setiap baris
        geometric_means = np.zeros(self.n)
        for i in range(self.n):
            product = 1.0
            for j in range(self.n):
                product *= self.pairwise_matrix[i, j]
            geometric_means[i] = product ** (1.0 / self.n)
        
        # Normalisasi
        total = np.sum(geometric_means)
        if total == 0:
            raise ValueError("Total geometric mean tidak boleh nol")
        
        self.eigenvector = geometric_means / total
        return self.eigenvector
    
    def calculate_lambda_max(self) -> float:
        """
        Menghitung lambda maksimum
        
        Returns:
            Nilai lambda maksimum
        """
        if self.eigenvector is None:
            self.calculate_eigenvector()
        
        if self.pairwise_matrix is None:
            raise ValueError("Matriks perbandingan belum di-set")
        
        # Hitung AW (matriks * eigenvector)
        aw = np.dot(self.pairwise_matrix, self.eigenvector)
        
        # Hitung lambda untuk setiap kriteria
        lambdas = []
        for i in range(self.n):
            if self.eigenvector[i] != 0:
                lambdas.append(aw[i] / self.eigenvector[i])
        
        self.lambda_max = np.mean(lambdas)
        return self.lambda_max
    
    def check_consistency(self) -> Tuple[float, float, bool]:
        """
        Uji konsistensi matriks perbandingan
        
        Returns:
            Tuple (CI, CR, is_consistent)
        """
        if self.lambda_max is None:
            self.calculate_lambda_max()
        
        # Hitung CI
        self.ci = (self.lambda_max - self.n) / (self.n - 1) if self.n > 1 else 0
        
        # Hitung CR
        ri = RI_TABLE.get(self.n, 1.58)
        self.cr = self.ci / ri if ri > 0 else 0
        
        # Matriks konsisten jika CR <= 0.1 (10%)
        is_consistent = self.cr <= 0.1
        
        return self.ci, self.cr, is_consistent
    
    def calculate_weights(self) -> Dict[str, float]:
        """
        Menghitung bobot kriteria dari matriks perbandingan
        
        Returns:
            Dictionary dengan nama kriteria sebagai key dan bobot sebagai value
        """
        if self.eigenvector is None:
            self.calculate_eigenvector()
        
        self.weights = {
            self.criteria_names[i]: float(self.eigenvector[i])
            for i in range(self.n)
        }
        
        return self.weights
    
    def get_results(self) -> Dict:
        """
        Mendapatkan semua hasil perhitungan AHP
        
        Returns:
            Dictionary berisi semua hasil perhitungan
        """
        if self.weights is None:
            self.calculate_weights()
        
        if self.ci is None or self.cr is None:
            self.check_consistency()
        
        return {
            'pairwise_matrix': self.pairwise_matrix.tolist() if self.pairwise_matrix is not None else None,
            'eigenvector': self.eigenvector.tolist() if self.eigenvector is not None else None,
            'lambda_max': float(self.lambda_max) if self.lambda_max is not None else None,
            'ci': float(self.ci) if self.ci is not None else None,
            'cr': float(self.cr) if self.cr is not None else None,
            'is_consistent': self.cr <= 0.1 if self.cr is not None else False,
            'weights': self.weights
        }


class FuzzyAHPCalculator:
    """Kelas untuk perhitungan Fuzzy AHP sesuai PDF"""
    
    def __init__(self, criteria_names: List[str]):
        """
        Inisialisasi Fuzzy AHP Calculator
        
        Args:
            criteria_names: List nama kriteria
        """
        self.criteria_names = criteria_names
        self.n = len(criteria_names)
        self.fuzzy_pairwise_matrix = None  # Matriks dengan TFN
        self.fuzzy_synthetic_extent = None
        self.fuzzy_weights = None
        self.normalized_weights = None
        
    def crisp_to_tfn(self, value: float) -> Tuple[float, float, float]:
        """
        Konversi nilai crisp ke Triangular Fuzzy Number
        
        Args:
            value: Nilai crisp (1-9)
            
        Returns:
            Tuple (l, m, u) untuk TFN
        """
        # Bulatkan ke nilai terdekat dalam skala 1-9
        rounded = max(1, min(9, round(value)))
        return TFN_SCALE.get(rounded, (1, 1, 1))
    
    def set_fuzzy_pairwise_matrix(self, matrix: np.ndarray):
        """
        Set matriks perbandingan berpasangan dan konversi ke TFN
        
        Args:
            matrix: Matriks n x n dengan nilai crisp (1-9)
        """
        if matrix.shape != (self.n, self.n):
            raise ValueError(f"Matrix harus berukuran {self.n}x{self.n}")
        
        # Konversi ke TFN
        fuzzy_matrix = np.zeros((self.n, self.n, 3), dtype=float)
        for i in range(self.n):
            for j in range(self.n):
                if i == j:
                    fuzzy_matrix[i, j] = (1, 1, 1)
                elif matrix[i, j] >= 1:
                    fuzzy_matrix[i, j] = self.crisp_to_tfn(matrix[i, j])
                else:
                    # Jika < 1, gunakan kebalikan
                    reciprocal_value = 1.0 / matrix[i, j]
                    tfn = self.crisp_to_tfn(reciprocal_value)
                    fuzzy_matrix[i, j] = get_tfn_reciprocal(tfn)
        
        self.fuzzy_pairwise_matrix = fuzzy_matrix
    
    def calculate_fuzzy_synthetic_extent(self) -> List[Tuple[float, float, float]]:
        """
        Menghitung Fuzzy Synthetic Extent (Si) untuk setiap kriteria
        
        Formula: Si = Σ M_gi^j [Σ Σ M_gi^j]^-1
        
        Returns:
            List of TFN (l, m, u) untuk setiap kriteria
        """
        if self.fuzzy_pairwise_matrix is None:
            raise ValueError("Matriks fuzzy perbandingan belum di-set")
        
        # Hitung jumlah kolom untuk setiap baris (Σ M_gi^j)
        row_sums = []
        for i in range(self.n):
            l_sum, m_sum, u_sum = 0, 0, 0
            for j in range(self.n):
                l, m, u = self.fuzzy_pairwise_matrix[i, j]
                l_sum += l
                m_sum += m
                u_sum += u
            row_sums.append((l_sum, m_sum, u_sum))
        
        # Hitung total semua (Σ Σ M_gi^j)
        total_l, total_m, total_u = 0, 0, 0
        for l, m, u in row_sums:
            total_l += l
            total_m += m
            total_u += u
        
        # Hitung Si untuk setiap kriteria
        synthetic_extents = []
        for l_sum, m_sum, u_sum in row_sums:
            # Si = (l_sum, m_sum, u_sum) / (total_l, total_m, total_u)
            # Untuk pembagian TFN: (l1, m1, u1) / (l2, m2, u2) = (l1/u2, m1/m2, u1/l2)
            if total_u > 0 and total_m > 0 and total_l > 0:
                si_l = l_sum / total_u
                si_m = m_sum / total_m
                si_u = u_sum / total_l
                synthetic_extents.append((si_l, si_m, si_u))
            else:
                synthetic_extents.append((0, 0, 0))
        
        self.fuzzy_synthetic_extent = synthetic_extents
        return synthetic_extents
    
    def compare_fuzzy_probability(self, m1: Tuple[float, float, float], 
                                   m2: Tuple[float, float, float]) -> float:
        """
        Menghitung probabilitas V(M2 >= M1)
        
        Formula:
        - V(M2 >= M1) = 1 jika m2 >= m1
        - V(M2 >= M1) = 0 jika l1 >= u2
        - V(M2 >= M1) = (l1 - u2) / ((m2 - u2) - (m1 - l1)) untuk kondisi lain
        
        Args:
            m1: TFN pertama (l1, m1, u1)
            m2: TFN kedua (l2, m2, u2)
            
        Returns:
            Nilai probabilitas V(M2 >= M1)
        """
        l1, m1_val, u1 = m1
        l2, m2_val, u2 = m2
        
        if m2_val >= m1_val:
            return 1.0
        elif l1 >= u2:
            return 0.0
        else:
            denominator = (m2_val - u2) - (m1_val - l1)
            if abs(denominator) < 1e-10:
                return 0.0
            return (l1 - u2) / denominator
    
    def calculate_fuzzy_weights(self) -> Dict[str, Tuple[float, float, float]]:
        """
        Menghitung bobot fuzzy menggunakan perbandingan probabilitas
        
        Returns:
            Dictionary dengan nama kriteria sebagai key dan TFN weight sebagai value
        """
        if self.fuzzy_synthetic_extent is None:
            self.calculate_fuzzy_synthetic_extent()
        
        # Hitung V(Si >= Sk) untuk semua k != i
        d_values = []
        for i in range(self.n):
            si = self.fuzzy_synthetic_extent[i]
            min_prob = float('inf')
            
            for k in range(self.n):
                if k != i:
                    sk = self.fuzzy_synthetic_extent[k]
                    prob = self.compare_fuzzy_probability(sk, si)
                    min_prob = min(min_prob, prob)
            
            d_values.append(min_prob)
        
        # Normalisasi d values
        total_d = sum(d_values)
        if total_d == 0:
            # Jika semua nol, beri bobot sama
            normalized_d = [1.0 / self.n] * self.n
        else:
            normalized_d = [d / total_d for d in d_values]
        
        # Simpan sebagai TFN (menggunakan nilai tengah dari synthetic extent)
        self.fuzzy_weights = {}
        self.normalized_weights = {}
        
        for i, name in enumerate(self.criteria_names):
            # Gunakan nilai tengah dari synthetic extent sebagai representasi
            si = self.fuzzy_synthetic_extent[i]
            self.fuzzy_weights[name] = si
            self.normalized_weights[name] = normalized_d[i]
        
        return self.normalized_weights
    
    def get_results(self) -> Dict:
        """
        Mendapatkan semua hasil perhitungan Fuzzy AHP
        
        Returns:
            Dictionary berisi semua hasil perhitungan
        """
        if self.normalized_weights is None:
            self.calculate_fuzzy_weights()
        
        return {
            'fuzzy_pairwise_matrix': self.fuzzy_pairwise_matrix.tolist() if self.fuzzy_pairwise_matrix is not None else None,
            'fuzzy_synthetic_extent': self.fuzzy_synthetic_extent,
            'fuzzy_weights': self.fuzzy_weights,
            'normalized_weights': self.normalized_weights
        }

