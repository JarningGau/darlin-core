"""
测试配置系统
"""

import numpy as np
from darlinpy.config import AmpliconConfig, get_original_carlin_config, ScoringConfig, get_default_scoring_config


class TestAmpliconConfig:
    
    def test_load_original_carlin(self):
        """测试加载原始CARLIN配置"""
        config = get_original_carlin_config()
        
        # 验证基本配置
        assert len(config.sequence.segments) == 10
        assert config.sequence.pam == "TGGAGTC"
        assert config.sequence.prefix == "CGCCG"
        assert config.sequence.postfix == "TGGGAGCT"
    
    def test_sequence_structure(self):
        """测试序列结构"""
        config = get_original_carlin_config()
        
        # 验证序列结构
        carlin_seq = config.carlin_sequence
        
        # 应该以prefix开始
        assert carlin_seq.startswith(config.sequence.prefix)
        
        # 应该以postfix结束
        assert carlin_seq.endswith(config.sequence.postfix)
        
        # 包含所有segments
        for segment in config.sequence.segments:
            assert segment in carlin_seq
        
        # 包含9个PAM序列 (最后一个segment后面没有PAM)
        pam_count = carlin_seq.count(config.sequence.pam)
        assert pam_count == 9
    
    def test_positions(self):
        """测试位置计算"""
        config = get_original_carlin_config()
        
        # 验证位置信息
        assert 'prefix' in config.positions
        assert 'postfix' in config.positions
        assert len(config.positions['segments']) == 10
        assert len(config.positions['cutsites']) == 10
        assert len(config.positions['consites']) == 10
        assert len(config.positions['pams']) == 9  # 只有9个PAM
        
        # 验证每个segment的consite和cutsite划分
        for i in range(10):
            segment_start, segment_end = config.positions['segments'][i]
            consite_start, consite_end = config.positions['consites'][i]
            cutsite_start, cutsite_end = config.positions['cutsites'][i]
            
            # Consite应该是segment的前13bp
            assert consite_start == segment_start
            assert consite_end == segment_start + 13
            
            # Cutsite应该是segment的后7bp
            assert cutsite_start == consite_end
            assert cutsite_end == segment_end
            assert cutsite_end - cutsite_start == 7
    
    def test_penalty_arrays(self):
        """测试惩罚数组"""
        config = get_original_carlin_config()
        
        open_penalty, close_penalty = config.get_penalty_arrays()
        
        # 验证数组长度
        expected_length = len(config.carlin_sequence) + 1
        assert len(open_penalty) == expected_length
        assert len(close_penalty) == expected_length
        
        # 验证数组类型
        assert open_penalty.dtype == np.float64
        assert close_penalty.dtype == np.float64
        
        # 验证惩罚值范围合理
        assert open_penalty.min() >= 0
        assert close_penalty.min() >= 0
        assert open_penalty.max() <= 20  # 合理的上限
        assert close_penalty.max() <= 20
    
    def test_motif_info(self):
        """测试motif信息查询"""
        config = get_original_carlin_config()
        
        # 测试prefix位置
        motif_info = config.get_motif_info(0)
        assert motif_info['type'] == 'prefix'
        
        # 测试第一个segment的consite
        segment_start = config.positions['segments'][0][0]
        motif_info = config.get_motif_info(segment_start + 5)  # consite内的位置
        assert motif_info['type'] == 'consite'
        assert motif_info['motif_id'] == 0
        
        # 测试第一个segment的cutsite
        cutsite_start = config.positions['cutsites'][0][0]
        motif_info = config.get_motif_info(cutsite_start + 2)  # cutsite内的位置
        assert motif_info['type'] == 'cutsite'
        assert motif_info['motif_id'] == 0
        
        # 测试第一个PAM
        if len(config.positions['pams']) > 0:
            pam_start = config.positions['pams'][0][0]
            motif_info = config.get_motif_info(pam_start + 2)  # PAM内的位置
            assert motif_info['type'] == 'pam'
            assert motif_info['motif_id'] == 0


class TestScoringConfig:
    
    def test_nuc44_matrix(self):
        """测试NUC44评分矩阵"""
        config = get_default_scoring_config()
        
        # 验证矩阵类型
        assert config.matrix_type == "nuc44"
        
        # 验证矩阵形状
        assert len(config.substitution_matrix) == 25  # 5x5矩阵打平
        
        # 验证匹配得分
        assert config.get_score(1, 1) == 5.0  # A-A匹配
        assert config.get_score(2, 2) == 5.0  # C-C匹配
        assert config.get_score(3, 3) == 5.0  # G-G匹配
        assert config.get_score(4, 4) == 5.0  # T-T匹配
        
        # 验证不匹配得分
        assert config.get_score(1, 2) == -4.0  # A-C不匹配
        assert config.get_score(1, 3) == -4.0  # A-G不匹配
        assert config.get_score(1, 4) == -4.0  # A-T不匹配
        
        # 验证gap得分
        assert config.get_score(0, 1) == 0.0  # gap-A
        assert config.get_score(1, 0) == 0.0  # A-gap
    
    def test_simple_matrix(self):
        """测试简单评分矩阵"""
        config = ScoringConfig("simple", match_score=10.0, mismatch_score=-2.0)
        
        # 验证自定义得分
        assert config.get_score(1, 1) == 10.0  # A-A匹配
        assert config.get_score(1, 2) == -2.0  # A-C不匹配
    
    def test_transition_transversion_matrix(self):
        """测试转换/颠换评分矩阵"""
        config = ScoringConfig("transition_transversion", 
                              match_score=5.0, 
                              transition_score=-1.0, 
                              transversion_score=-4.0)
        
        # 验证匹配
        assert config.get_score(1, 1) == 5.0  # A-A匹配
        
        # 验证转换 (A<->G, C<->T)
        assert config.get_score(1, 3) == -1.0  # A-G转换
        assert config.get_score(3, 1) == -1.0  # G-A转换
        assert config.get_score(2, 4) == -1.0  # C-T转换
        assert config.get_score(4, 2) == -1.0  # T-C转换
        
        # 验证颠换
        assert config.get_score(1, 2) == -4.0  # A-C颠换
        assert config.get_score(1, 4) == -4.0  # A-T颠换

