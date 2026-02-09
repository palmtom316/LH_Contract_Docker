import request from '@/utils/request'

/**
 * 合同搜索 API
 * 用于查询机器人功能
 */

/**
 * 模糊搜索合同
 * @param {Object} params - 搜索参数
 * @param {string} params.query - 搜索关键词（合同序号、名称或编号）
 * @param {string} params.companyCategory - 公司合同分类
 * @param {string} params.partyAName - 上游合同甲方单位
 * @param {string} params.partyBName - 下游/管理合同乙方单位
 * @param {string} params.signDateStart - 签约时间开始日期（YYYY-MM-DD）
 * @param {string} params.signDateEnd - 签约时间结束日期（YYYY-MM-DD）
 * @param {number} params.limit - 返回结果数量限制（为空不限制）
 * @returns {Promise} 搜索结果
 */
export function searchContracts({
  query = '',
  companyCategory = '',
  partyAName = '',
  partyBName = '',
  signDateStart = '',
  signDateEnd = '',
  limit
} = {}) {
  const params = {
    query,
    company_category: companyCategory,
    party_a_name: partyAName,
    party_b_name: partyBName
  }
  if (signDateStart) {
    params.sign_date_start = signDateStart
  }
  if (signDateEnd) {
    params.sign_date_end = signDateEnd
  }
  if (limit != null) {
    params.limit = limit
  }
  return request({
    url: '/contracts/search',
    method: 'get',
    params
  })
}
