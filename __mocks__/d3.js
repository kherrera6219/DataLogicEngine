// Mock d3 for Jest tests
module.exports = {
  select: jest.fn(() => ({
    selectAll: jest.fn(() => ({
      data: jest.fn(() => ({
        enter: jest.fn(() => ({
          append: jest.fn(() => ({
            attr: jest.fn(),
            style: jest.fn(),
            text: jest.fn(),
          })),
        })),
        exit: jest.fn(() => ({
          remove: jest.fn(),
        })),
      })),
      attr: jest.fn(),
      style: jest.fn(),
      text: jest.fn(),
    })),
    append: jest.fn(() => ({
      attr: jest.fn(),
      style: jest.fn(),
      text: jest.fn(),
    })),
    attr: jest.fn(),
    style: jest.fn(),
  })),
  scaleLinear: jest.fn(() => ({
    domain: jest.fn().mockReturnThis(),
    range: jest.fn().mockReturnThis(),
  })),
  scaleTime: jest.fn(() => ({
    domain: jest.fn().mockReturnThis(),
    range: jest.fn().mockReturnThis(),
  })),
  axisBottom: jest.fn(),
  axisLeft: jest.fn(),
  line: jest.fn(() => ({
    x: jest.fn().mockReturnThis(),
    y: jest.fn().mockReturnThis(),
  })),
  extent: jest.fn(() => [0, 100]),
  max: jest.fn(() => 100),
  min: jest.fn(() => 0),
}
