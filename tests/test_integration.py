"""
集成测试 - 验证CARLIN比对系统的端到端功能
"""

from darlin_core.alignment import CARLINAligner, align_to_carlin, create_default_aligner
from darlin_core.config import get_original_carlin_config


class TestCARLINIntegration:
    
    def test_end_to_end_perfect_sequence(self):
        """测试完美序列的端到端比对"""
        # 获取参考序列
        config = get_original_carlin_config()
        perfect_seq = config.get_reference_sequence()
        
        # 使用便捷函数比对
        result = align_to_carlin(perfect_seq, verbose=False)
        
        # 验证完美匹配
        assert result['alignment_score'] > 1300  # 高分
        assert result['statistics']['identity'] == 1.0  # 100%一致性
        assert result['statistics']['matches'] == len(perfect_seq)
        assert result['statistics']['mismatches'] == 0
        assert result['statistics']['query_gaps'] == 0
        assert result['statistics']['reference_gaps'] == 0
        
    def test_end_to_end_mutated_sequence(self):
        """测试带突变序列的端到端比对"""
        config = get_original_carlin_config()
        original_seq = config.get_reference_sequence()
        
        # 引入一些突变
        mutated_seq = (
            original_seq[:50] + "TTTT" +  # 插入
            original_seq[50:100] +        # 保持不变
            original_seq[103:200] +       # 删除3bp
            "A" + original_seq[201:]      # 替换
        )
        
        # 比对突变序列
        result = align_to_carlin(mutated_seq, verbose=False)
        
        # 验证能够处理突变
        assert result['alignment_score'] > 1000  # 仍然有较高分数
        assert result['statistics']['identity'] < 1.0  # 不是完美匹配
        assert result['statistics']['identity'] > 0.9   # 但一致性仍然很高
        
        # 应该检测到gap和不匹配
        stats = result['statistics']
        total_differences = stats['query_gaps'] + stats['reference_gaps'] + stats['mismatches']
        assert total_differences > 0
        
    def test_batch_processing(self):
        """测试批量处理功能"""
        config = get_original_carlin_config()
        ref_seq = config.get_reference_sequence()
        
        # 创建测试序列集
        test_sequences = [
            ref_seq,                                    # 完美序列
            ref_seq[:200],                             # 截断序列
            ref_seq[:100] + "AAAA" + ref_seq[100:],   # 插入序列
            ref_seq[:150] + ref_seq[160:],            # 删除序列
            ref_seq.replace(ref_seq[50:60], "N"*10),  # 含N序列
        ]
        
        # 批量比对
        aligner = create_default_aligner()
        results = aligner.align_sequences(test_sequences, verbose=False)
        
        # 验证所有序列都成功比对
        assert len(results) == len(test_sequences)
        
        successful_results = [r for r in results if 'error' not in r]
        assert len(successful_results) >= 4  # 至少4个成功（N序列可能失败）
        
        # 验证完美序列得分最高
        perfect_result = results[0]
        assert 'error' not in perfect_result
        assert perfect_result['statistics']['identity'] == 1.0
        
        # 验证其他序列得分合理
        for i, result in enumerate(results[1:], 1):
            if 'error' not in result:
                assert result['alignment_score'] > 0
                assert 0 <= result['statistics']['identity'] <= 1.0
        
    def test_config_integration(self):
        """测试配置系统集成"""
        # 测试配置加载
        config = get_original_carlin_config()
        assert len(config.sequence.segments) == 10
        assert config.sequence.pam == "TGGAGTC"
        
        # 测试比对器使用配置
        aligner = CARLINAligner()
        assert aligner.amplicon_config is not None
        assert aligner.scoring_config is not None
        assert len(aligner.reference_sequence) > 200
        
        # 验证惩罚数组长度匹配
        assert len(aligner.open_penalty_array) == len(aligner.reference_sequence) + 1
        assert len(aligner.close_penalty_array) == len(aligner.reference_sequence) + 1
        
    def test_motif_analysis(self):
        """测试motif级别的分析"""
        config = get_original_carlin_config()
        ref_seq = config.get_reference_sequence()
        
        # 在特定cutsite引入编辑
        cutsite_start, cutsite_end = config.positions['cutsites'][0]
        edited_seq = ref_seq[:cutsite_start+2] + "AGCT" + ref_seq[cutsite_start+2:]
        
        # 比对编辑序列
        aligner = create_default_aligner()
        result = aligner.align_sequence(edited_seq, verbose=False)
        
        # 验证motif分析结果
        motif_analysis = result['motif_analysis']
        assert 'prefix' in motif_analysis
        assert 'segments' in motif_analysis
        assert 'pams' in motif_analysis
        assert 'postfix' in motif_analysis
        
        # 应该在segments中检测到变化
        segments_stats = motif_analysis['segments']
        assert len(segments_stats) == 10
        
    def test_position_specific_penalties(self):
        """测试位置特异性惩罚的效果"""
        config = get_original_carlin_config()
        ref_seq = config.get_reference_sequence()
        
        # 在不同区域插入相同序列
        insertion = "AAAA"
        
        # 在cutsite区域插入 (应该惩罚较低)
        cutsite_pos = config.positions['cutsites'][0][0] + 2
        cutsite_seq = ref_seq[:cutsite_pos] + insertion + ref_seq[cutsite_pos:]
        
        # 在consite区域插入 (应该惩罚较高)
        consite_pos = config.positions['consites'][0][0] + 2
        consite_seq = ref_seq[:consite_pos] + insertion + ref_seq[consite_pos:]
        
        # 比对两个序列
        aligner = create_default_aligner()
        cutsite_result = aligner.align_sequence(cutsite_seq, verbose=False)
        consite_result = aligner.align_sequence(consite_seq, verbose=False)
        
        # cutsite插入应该比consite插入得分更高 (惩罚更低)
        cutsite_score = cutsite_result['alignment_score']
        consite_score = consite_result['alignment_score']
        
        assert cutsite_score > consite_score
        
    def test_error_handling(self):
        """测试错误处理"""
        aligner = create_default_aligner()
        
        # 测试无效序列
        try:
            result = aligner.align_sequence("", verbose=False)
            assert False, "应该抛出异常"
        except ValueError:
            pass  # 预期的异常
        
        # 测试包含无效字符的序列
        try:
            result = aligner.align_sequence("ACGTXYZ", verbose=False)
            assert False, "应该抛出异常"  
        except ValueError:
            pass  # 预期的异常
        
        # 测试正常序列不会抛出异常
        config = get_original_carlin_config()
        ref_seq = config.get_reference_sequence()
        
        try:
            result = aligner.align_sequence(ref_seq, verbose=False)
            assert 'error' not in result
        except Exception as e:
            assert False, f"正常序列不应该抛出异常: {e}"
        
